#!/usr/bin/env python3
"""Isolated TEST_ONLY HTTP fixtures for M5 R2 Browser UAT."""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB_ROOT))

from frontend_server import create_frontend_server  # noqa: E402

DATASET_ID = "NASA_CMAPSS_FD001"
SOURCE_TYPE = "NASA_FD001_LOCAL_TRUSTED"
TRAIN_SHA = "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8"


class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, payload: object, status: int = 200, raw: bytes | None = None) -> None:
        body = raw if raw is not None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def error_handler(status: int) -> type[QuietHandler]:
    titles = {
        400: ("INVALID_QUERY_VALUE", "TEST_ONLY query validation error"),
        404: ("OBSERVATION_NOT_FOUND", "TEST_ONLY observation not found"),
        503: ("SOURCE_NOT_VALIDATED", "TEST_ONLY source not validated"),
    }

    class ErrorHandler(QuietHandler):
        def do_GET(self) -> None:
            code, message = titles[status]
            self.send_json({"error": {"code": code, "message": message, "query": {}}}, status)

    return ErrorHandler


def null_handler(variant: str) -> type[QuietHandler]:
    class NullHandler(QuietHandler):
        def do_GET(self) -> None:
            if self.path == "/api/health":
                if variant == "invalid_source":
                    self.send_json({"error": {"code": "SOURCE_NOT_VALIDATED", "message": "TEST_ONLY source validation failure", "query": {}}}, 503)
                else:
                    self.send_json({"status": "ok", "dataset_id": DATASET_ID, "source_type": SOURCE_TYPE, "data_validated": True, "read_only": True})
                return
            if self.path == "/api/catalog":
                self.send_json({"dataset_id": DATASET_ID, "source_type": SOURCE_TYPE, "available_splits": ["TRAIN", "TEST"], "sensor_names": [f"sensor_{number}" for number in range(1, 22)]})
                return
            if self.path.startswith("/api/units"):
                self.send_json({"dataset_id": DATASET_ID, "source_type": SOURCE_TYPE, "split": "TRAIN", "units": [{"unit_id": 1, "min_cycle": 1, "max_cycle": 20, "observation_count": 20}]})
                return
            if self.path.startswith("/api/history"):
                observation = {
                    "cycle": 1,
                    "sensor": "sensor_7",
                    "value": 554.36,
                    "optional_note": None,
                    "source_evidence": {
                        "source_file": "train_FD001.txt",
                        "source_sha256": TRAIN_SHA,
                        "source_physical_line_1_based": 1,
                        "parsed_row_index_0_based": 0,
                    },
                }
                if variant == "required_null":
                    observation["value"] = None
                elif variant == "missing_required":
                    observation.pop("value")
                payload = {
                    "dataset_id": DATASET_ID,
                    "source_type": SOURCE_TYPE,
                    "split": "TRAIN",
                    "unit_id": 1,
                    "sensor": "sensor_7",
                    "start_cycle": 1,
                    "end_cycle": 20,
                    "observation_count": 1,
                    "observations": [observation],
                }
                if variant == "non_finite":
                    raw = json.dumps(payload).replace('"value": 554.36', '"value": 1e999').encode("utf-8")
                    self.send_json({}, raw=raw)
                else:
                    self.send_json(payload)
                return
            self.send_json({"error": {"code": "NOT_FOUND", "message": "TEST_ONLY", "query": {}}}, 404)

    return NullHandler


def start_fixtures() -> tuple[list[ThreadingHTTPServer], list[threading.Thread], dict[str, int]]:
    static_dir = WEB_ROOT / "frontend"
    variants = {
        "error_400": (8210, 8211, error_handler(400)),
        "error_404": (8212, 8213, error_handler(404)),
        "error_503": (8214, 8215, error_handler(503)),
        "required_null": (8220, 8221, null_handler("required_null")),
        "missing_required": (8222, 8223, null_handler("missing_required")),
        "non_finite": (8224, 8225, null_handler("non_finite")),
        "invalid_source": (8226, 8227, null_handler("invalid_source")),
        "optional_null": (8228, 8229, null_handler("optional_null")),
    }
    servers: list[ThreadingHTTPServer] = []
    threads: list[threading.Thread] = []
    frontends: dict[str, int] = {}
    for name, (api_port, frontend_port, handler) in variants.items():
        api = ThreadingHTTPServer(("127.0.0.1", api_port), handler)
        frontend = create_frontend_server(static_dir, port=frontend_port, api_port=api_port)
        servers.extend((api, frontend))
        frontends[name] = frontend_port
    for server in servers:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        threads.append(thread)
    return servers, threads, frontends


def stop_fixtures(servers: list[ThreadingHTTPServer], threads: list[threading.Thread]) -> None:
    for server in servers:
        server.shutdown()
        server.server_close()
    for thread in threads:
        thread.join(timeout=5)


if __name__ == "__main__":
    active_servers, active_threads, ports = start_fixtures()
    print(json.dumps({"boundary": "TEST_ONLY", "frontends": ports}, sort_keys=True), flush=True)
    try:
        active_threads[0].join()
    except KeyboardInterrupt:
        pass
    finally:
        stop_fixtures(active_servers, active_threads)
