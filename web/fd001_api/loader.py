"""Strict, read-only FD001 source validation and query support."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Final


DATASET_ID: Final = "NASA_CMAPSS_FD001"
SOURCE_TYPE: Final = "NASA_FD001_LOCAL_TRUSTED"
EXPECTED_HASHES: Final = {
    "train_FD001.txt": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "test_FD001.txt": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
    "RUL_FD001.txt": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
}


class SourceValidationError(Exception):
    """Raised when trusted source validation fails.

    Messages are deliberately safe for API responses: they never include a
    local absolute path or a raw source row.
    """


@dataclass(frozen=True)
class SourceEvidence:
    source_file: str
    source_sha256: str
    source_physical_line_1_based: int
    parsed_row_index_0_based: int

    def as_dict(self) -> dict[str, object]:
        return {
            "source_file": self.source_file,
            "source_sha256": self.source_sha256,
            "source_physical_line_1_based": self.source_physical_line_1_based,
            "parsed_row_index_0_based": self.parsed_row_index_0_based,
        }


@dataclass(frozen=True)
class Observation:
    unit_id: int
    cycle: int
    sensors: tuple[float, ...]
    evidence: SourceEvidence


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _positive_integer(token: str, field: str, source_file: str, line: int) -> int:
    try:
        value = int(token)
    except ValueError as exc:
        raise SourceValidationError(
            f"{source_file} has an invalid {field} at physical line {line}"
        ) from exc
    if str(value) != token and token not in {f"+{value}"}:
        raise SourceValidationError(
            f"{source_file} has a non-integer {field} at physical line {line}"
        )
    if value <= 0:
        raise SourceValidationError(
            f"{source_file} has a non-positive {field} at physical line {line}"
        )
    return value


class FD001Dataset:
    """Validated in-memory index built without modifying source files."""

    def __init__(self, data_dir: Path | str):
        self._data_dir = Path(data_dir)
        self.validated = False
        self.validation_error: str | None = None
        self._rows: dict[str, dict[int, tuple[Observation, ...]]] = {}
        self._hashes: dict[str, str] = {}
        self._rul: dict[int, int] = {}
        try:
            self._load_all()
        except (OSError, SourceValidationError) as exc:
            self.validation_error = self._safe_error(exc)
            self._rows.clear()
            self._rul.clear()
        else:
            self.validated = True

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        if isinstance(exc, SourceValidationError):
            return str(exc)
        return "A required FD001 source file is missing or unreadable"

    def _validate_hash(self, filename: str) -> tuple[Path, str]:
        path = self._data_dir / filename
        actual = _file_sha256(path)
        if actual != EXPECTED_HASHES[filename]:
            raise SourceValidationError(f"{filename} SHA-256 does not match the accepted contract")
        self._hashes[filename] = actual
        return path, actual

    def _load_split(self, split: str, filename: str) -> None:
        path, source_hash = self._validate_hash(filename)
        by_unit: dict[int, list[Observation]] = {}
        seen_keys: set[tuple[int, int]] = set()
        parsed_index = 0

        with path.open("r", encoding="utf-8", newline="") as source:
            for physical_line, raw_line in enumerate(source, start=1):
                fields = raw_line.split()
                if len(fields) != 26:
                    raise SourceValidationError(
                        f"{filename} has an invalid field count at physical line {physical_line}"
                    )
                unit_id = _positive_integer(fields[0], "unit_id", filename, physical_line)
                cycle = _positive_integer(fields[1], "cycle", filename, physical_line)
                key = (unit_id, cycle)
                if key in seen_keys:
                    raise SourceValidationError(
                        f"{filename} has a duplicate Unit-Cycle at physical line {physical_line}"
                    )
                seen_keys.add(key)

                try:
                    numeric_values = tuple(float(token) for token in fields[2:])
                except ValueError as exc:
                    raise SourceValidationError(
                        f"{filename} has a malformed numeric value at physical line {physical_line}"
                    ) from exc
                if len(numeric_values) != 24 or not all(isfinite(value) for value in numeric_values):
                    raise SourceValidationError(
                        f"{filename} has a missing or non-finite required value at physical line {physical_line}"
                    )

                current_rows = by_unit.setdefault(unit_id, [])
                expected_cycle = len(current_rows) + 1
                if cycle != expected_cycle:
                    raise SourceValidationError(
                        f"{filename} has a non-contiguous cycle at physical line {physical_line}"
                    )
                current_rows.append(
                    Observation(
                        unit_id=unit_id,
                        cycle=cycle,
                        sensors=numeric_values[3:],
                        evidence=SourceEvidence(
                            source_file=filename,
                            source_sha256=source_hash,
                            source_physical_line_1_based=physical_line,
                            parsed_row_index_0_based=parsed_index,
                        ),
                    )
                )
                parsed_index += 1

        if not by_unit:
            raise SourceValidationError(f"{filename} contains no observations")
        self._rows[split] = {unit: tuple(rows) for unit, rows in by_unit.items()}

    def _load_rul(self) -> None:
        filename = "RUL_FD001.txt"
        path, _ = self._validate_hash(filename)
        labels: list[int] = []
        with path.open("r", encoding="utf-8", newline="") as source:
            for physical_line, raw_line in enumerate(source, start=1):
                fields = raw_line.split()
                if len(fields) != 1:
                    raise SourceValidationError(
                        f"{filename} has an invalid field count at physical line {physical_line}"
                    )
                try:
                    value = int(fields[0])
                except ValueError as exc:
                    raise SourceValidationError(
                        f"{filename} has an invalid label at physical line {physical_line}"
                    ) from exc
                if str(value) != fields[0] or value < 0:
                    raise SourceValidationError(
                        f"{filename} has an invalid label at physical line {physical_line}"
                    )
                labels.append(value)

        test_units = sorted(self._rows["TEST"])
        if test_units != list(range(1, len(test_units) + 1)) or len(labels) != len(test_units):
            raise SourceValidationError("RUL_FD001.txt does not match the positional TEST Unit mapping")
        self._rul = {unit_id: labels[unit_id - 1] for unit_id in test_units}

    def _load_all(self) -> None:
        self._load_split("TRAIN", "train_FD001.txt")
        self._load_split("TEST", "test_FD001.txt")
        self._load_rul()

    def units(self, split: str) -> list[dict[str, int]]:
        return [
            {
                "unit_id": unit_id,
                "min_cycle": rows[0].cycle,
                "max_cycle": rows[-1].cycle,
                "observation_count": len(rows),
            }
            for unit_id, rows in sorted(self._rows[split].items())
        ]

    def history(self, split: str, unit_id: int, sensor: int, start: int, end: int) -> list[dict[str, object]]:
        rows = self._rows[split].get(unit_id)
        if rows is None or start < 1 or end > len(rows):
            return []
        sensor_name = f"sensor_{sensor}"
        return [
            {
                "cycle": row.cycle,
                "sensor": sensor_name,
                "value": row.sensors[sensor - 1],
                "source_evidence": row.evidence.as_dict(),
            }
            for row in rows[start - 1 : end]
        ]

    @property
    def hashes(self) -> dict[str, str]:
        return dict(self._hashes)
