"""Local-only JSON HTTP server for the validated FD001 dataset."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .loader import DATASET_ID, SOURCE_TYPE, FD001Dataset


def _error(code: str, message: str, query: dict[str, object] | None = None) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "query": query or {}}}


def _observation_schema() -> list[dict[str, object]]:
    fields = [
        {
            "name": "unit_id",
            "data_type": "integer",
            "nullable": False,
            "source_column_position": 1,
            "query_semantics": "Positive split-scoped engine identifier.",
        },
        {
            "name": "cycle",
            "data_type": "integer",
            "nullable": False,
            "source_column_position": 2,
            "query_semantics": (
                "Positive contiguous observation sequence beginning at 1 within each Unit."
            ),
        },
    ]
    fields.extend(
        {
            "name": f"setting_{number}",
            "data_type": "number",
            "nullable": False,
            "source_column_position": number + 2,
            "query_semantics": (
                "Operating setting channel with source-defined or unspecified physical units."
            ),
        }
        for number in range(1, 4)
    )
    fields.extend(
        {
            "name": f"sensor_{number}",
            "data_type": "number",
            "nullable": False,
            "source_column_position": number + 5,
            "query_semantics": (
                "Sensor channel with source-defined or unspecified physical units."
            ),
        }
        for number in range(1, 22)
    )
    return fields


class FD001RequestHandler(BaseHTTPRequestHandler):
    dataset: FD001Dataset
    server_version = "FD001ReadOnlyAPI/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _source_ready(self) -> bool:
        if self.dataset.validated:
            return True
        self._send(
            HTTPStatus.SERVICE_UNAVAILABLE,
            _error("SOURCE_NOT_VALIDATED", self.dataset.validation_error or "FD001 source validation failed"),
        )
        return False

    @staticmethod
    def _query(url_query: str) -> tuple[dict[str, str] | None, dict[str, object] | None]:
        raw = parse_qs(url_query, keep_blank_values=True)
        if any(len(values) != 1 for values in raw.values()):
            return None, _error("INVALID_QUERY_VALUE", "Query parameters must not be repeated")
        return {key: values[0] for key, values in raw.items()}, None

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        query, query_error = self._query(parsed.query)
        if query_error is not None:
            self._send(HTTPStatus.BAD_REQUEST, query_error)
            return
        assert query is not None

        if parsed.path == "/api/health":
            if not self._allow_parameters(query, set()):
                return
            self._health()
        elif parsed.path == "/api/catalog":
            if not self._allow_parameters(query, set()):
                return
            self._catalog()
        elif parsed.path == "/api/units":
            if not self._allow_parameters(query, {"split"}):
                return
            self._units(query)
        elif parsed.path == "/api/history":
            if not self._allow_parameters(query, {"split", "unit", "sensor", "start", "end"}):
                return
            self._history(query)
        else:
            self._send(HTTPStatus.NOT_FOUND, _error("NOT_FOUND", "Endpoint not found"))

    def _allow_parameters(self, query: dict[str, str], allowed: set[str]) -> bool:
        unknown = sorted(set(query) - allowed)
        if not unknown:
            return True
        self._send(
            HTTPStatus.BAD_REQUEST,
            _error(
                "INVALID_QUERY_VALUE",
                f"Unknown query parameter: {unknown[0]}",
                query,
            ),
        )
        return False

    def _health(self) -> None:
        if not self._source_ready():
            return
        self._send(
            HTTPStatus.OK,
            {
                "status": "ok",
                "dataset_id": DATASET_ID,
                "source_type": SOURCE_TYPE,
                "data_validated": True,
                "read_only": True,
            },
        )

    def _catalog(self) -> None:
        if not self._source_ready():
            return
        self._send(
            HTTPStatus.OK,
            {
                "dataset_id": DATASET_ID,
                "source_type": SOURCE_TYPE,
                "available_splits": ["TRAIN", "TEST"],
                "observation_schema": _observation_schema(),
                "operating_settings": [f"setting_{number}" for number in range(1, 4)],
                "sensor_names": [f"sensor_{number}" for number in range(1, 22)],
                "sensor_units": "source-defined/unspecified",
                "source_provenance": {
                    "evidence_fields": [
                        "source_file",
                        "source_sha256",
                        "source_physical_line_1_based",
                        "parsed_row_index_0_based",
                    ],
                    "test_rul": "Independent positional labels; not a Sensor History Split",
                },
            },
        )

    @staticmethod
    def _split(query: dict[str, str]) -> tuple[str | None, dict[str, object] | None]:
        if "split" not in query:
            return None, _error("INVALID_QUERY_VALUE", "Missing required parameter: split", query)
        split = query["split"].upper()
        if split not in {"TRAIN", "TEST"}:
            return None, _error("INVALID_SPLIT", "split must be train or test", query)
        return split, None

    def _units(self, query: dict[str, str]) -> None:
        if not self._source_ready():
            return
        split, error = self._split(query)
        if error is not None:
            self._send(HTTPStatus.BAD_REQUEST, error)
            return
        assert split is not None
        self._send(
            HTTPStatus.OK,
            {
                "dataset_id": DATASET_ID,
                "source_type": SOURCE_TYPE,
                "split": split,
                "units": self.dataset.units(split),
            },
        )

    @staticmethod
    def _integer(query: dict[str, str], name: str) -> tuple[int | None, dict[str, object] | None]:
        if name not in query:
            return None, _error("INVALID_QUERY_VALUE", f"Missing required parameter: {name}", query)
        try:
            value = int(query[name])
        except ValueError:
            return None, _error("INVALID_QUERY_VALUE", f"{name} must be a positive integer", query)
        if value <= 0 or str(value) != query[name]:
            return None, _error("INVALID_QUERY_VALUE", f"{name} must be a positive integer", query)
        return value, None

    @staticmethod
    def _sensor(query: dict[str, str]) -> tuple[int | None, dict[str, object] | None]:
        name = "sensor"
        if name not in query:
            return None, _error("INVALID_QUERY_VALUE", "Missing required parameter: sensor", query)
        try:
            value = int(query[name])
        except ValueError:
            return None, _error("INVALID_QUERY_VALUE", "sensor must be an integer", query)
        if str(value) != query[name]:
            return None, _error("INVALID_QUERY_VALUE", "sensor must be an integer", query)
        if not 1 <= value <= 21:
            return None, _error("INVALID_SENSOR", "sensor must be between 1 and 21", query)
        return value, None

    def _history(self, query: dict[str, str]) -> None:
        if not self._source_ready():
            return
        split, error = self._split(query)
        if error is not None:
            self._send(HTTPStatus.BAD_REQUEST, error)
            return
        values: dict[str, int] = {}
        for name in ("unit", "start", "end"):
            value, error = self._integer(query, name)
            if error is not None:
                self._send(HTTPStatus.BAD_REQUEST, error)
                return
            assert value is not None
            values[name] = value
        sensor, error = self._sensor(query)
        if error is not None:
            self._send(HTTPStatus.BAD_REQUEST, error)
            return
        assert sensor is not None
        values["sensor"] = sensor
        if values["start"] > values["end"]:
            self._send(HTTPStatus.BAD_REQUEST, _error("INVALID_QUERY_VALUE", "start must not exceed end", query))
            return

        assert split is not None
        unit_ids = {item["unit_id"] for item in self.dataset.units(split)}
        if values["unit"] not in unit_ids:
            self._send(HTTPStatus.NOT_FOUND, _error("OBSERVATION_NOT_FOUND", "Unit was not found", query))
            return
        observations = self.dataset.history(
            split, values["unit"], values["sensor"], values["start"], values["end"]
        )
        if not observations:
            self._send(HTTPStatus.NOT_FOUND, _error("OBSERVATION_NOT_FOUND", "Cycle range was not found", query))
            return
        self._send(
            HTTPStatus.OK,
            {
                "dataset_id": DATASET_ID,
                "source_type": SOURCE_TYPE,
                "split": split,
                "unit_id": values["unit"],
                "sensor": f"sensor_{values['sensor']}",
                "start_cycle": values["start"],
                "end_cycle": values["end"],
                "observation_count": len(observations),
                "observations": observations,
            },
        )

    def _read_only(self) -> None:
        self._send(
            HTTPStatus.METHOD_NOT_ALLOWED,
            _error("METHOD_NOT_ALLOWED", "This API is read-only"),
        )

    do_POST = _read_only
    do_PUT = _read_only
    do_PATCH = _read_only
    do_DELETE = _read_only


def create_server(data_dir: Path | str, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    dataset = FD001Dataset(data_dir)
    handler = type("BoundFD001RequestHandler", (FD001RequestHandler,), {"dataset": dataset})
    return ThreadingHTTPServer((host, port), handler)
