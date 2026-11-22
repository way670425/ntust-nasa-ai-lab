#!/usr/bin/env python3
"""Independent full-row Data Validation Gate for existing M2-A artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data" / "FD001"
OUTPUT = ROOT / "research" / "m2" / "m2a" / "output"
EXPECTED = {
    "train": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "test": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
    "rul": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate(status: str, checked: int, failures: list[dict[str, Any]], detail: str) -> dict[str, Any]:
    return {"status": status, "checked_records": checked, "failure_count": len(failures), "failures": failures[:20], "detail": detail}


def validate_observations(split: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[int, list[int]]]:
    source = DATA / f"{split}_FD001.txt"
    index_path = OUTPUT / f"{split}_raw_index.csv"
    failures: dict[str, list[dict[str, Any]]] = {
        "schema": [],
        "raw_index": [],
        "unit_cycle": [],
        "settings": [],
        "sensors": [],
    }
    source_hash = digest(source)
    if source_hash != EXPECTED[split]:
        failures["schema"].append({"reason": "FILE_HASH_MISMATCH", "actual": source_hash})

    with source.open("r", encoding="ascii", newline="") as handle:
        raw_lines = list(handle)
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        index_rows = list(csv.DictReader(handle))
    if len(raw_lines) != len(index_rows):
        failures["raw_index"].append({"reason": "RECORD_COUNT", "source": len(raw_lines), "index": len(index_rows)})

    by_unit: dict[int, list[int]] = defaultdict(list)
    seen: set[tuple[int, int]] = set()
    parsed: list[dict[str, Any]] = []
    for position, raw in enumerate(raw_lines, start=1):
        tokens = raw.split()
        if len(tokens) != 26:
            failures["schema"].append({"physical_line": position, "reason": "FIELD_COUNT", "actual": len(tokens)})
            continue
        try:
            unit = int(tokens[0])
            cycle = int(tokens[1])
            settings = [float(value) for value in tokens[2:5]]
            sensors = [float(value) for value in tokens[5:26]]
        except ValueError as exc:
            failures["schema"].append({"physical_line": position, "reason": "NUMERIC_PARSE", "detail": str(exc)})
            continue
        if len(settings) != 3 or any(not math.isfinite(value) for value in settings):
            failures["settings"].append({"physical_line": position, "values": tokens[2:5]})
        if len(sensors) != 21 or any(not math.isfinite(value) for value in sensors):
            failures["sensors"].append({"physical_line": position, "values": tokens[5:26]})
        key = (unit, cycle)
        if key in seen:
            failures["unit_cycle"].append({"physical_line": position, "reason": "DUPLICATE_KEY", "key": key})
        seen.add(key)
        by_unit[unit].append(cycle)
        parsed.append({"unit": unit, "cycle": cycle})

        if position <= len(index_rows):
            idx = index_rows[position - 1]
            expected_index = {
                "dataset_id": "NASA_CMAPSS_FD001",
                "split": split,
                "source_file": str(source.resolve()),
                "source_sha256": source_hash,
                "physical_line_number": str(position),
                "parsed_row_index": str(position - 1),
                "unit_id": str(unit),
                "cycle": str(cycle),
            }
            mismatches = {name: {"expected": value, "actual": idx.get(name)} for name, value in expected_index.items() if idx.get(name) != value}
            if mismatches:
                failures["raw_index"].append({"physical_line": position, "mismatches": mismatches})

    units = sorted(by_unit)
    if units != list(range(1, 101)):
        failures["unit_cycle"].append({"reason": "UNIT_SET", "actual": units})
    for unit, cycles in by_unit.items():
        expected_cycles = list(range(1, len(cycles) + 1))
        if cycles != expected_cycles:
            failures["unit_cycle"].append({"reason": "CYCLE_SEQUENCE", "unit": unit, "actual_first": cycles[:5], "actual_last": cycles[-5:]})

    gates = {
        "SCHEMA_VALIDATION": gate("PASS" if not failures["schema"] else "FAIL", len(raw_lines), failures["schema"], "26 fields; integer Unit/Cycle; remaining fields finite numeric"),
        "RAW_INDEX_VALIDATION": gate("PASS" if not failures["raw_index"] else "FAIL", min(len(raw_lines), len(index_rows)), failures["raw_index"], "every source row matched every index field"),
        "UNIT_CYCLE_VALIDATION": gate("PASS" if not failures["unit_cycle"] else "FAIL", len(raw_lines), failures["unit_cycle"], "Units 1-100; unique keys; source-order cycles contiguous from 1"),
        "SETTINGS_VALIDATION": gate("PASS" if not failures["settings"] else "FAIL", len(raw_lines), failures["settings"], "exactly 3 finite numeric settings per observation"),
        "SENSOR_VALIDATION": gate("PASS" if not failures["sensors"] else "FAIL", len(raw_lines), failures["sensors"], "exactly 21 finite numeric sensor values per observation"),
    }
    return gates, parsed, by_unit


def validate_rul(test_units: list[int]) -> dict[str, Any]:
    source = DATA / "RUL_FD001.txt"
    index_path = OUTPUT / "rul_raw_index.csv"
    failures: list[dict[str, Any]] = []
    source_hash = digest(source)
    if source_hash != EXPECTED["rul"]:
        failures.append({"reason": "FILE_HASH_MISMATCH", "actual": source_hash})
    with source.open("r", encoding="ascii", newline="") as handle:
        raw_lines = list(handle)
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        index_rows = list(csv.DictReader(handle))
    if len(raw_lines) != 100 or len(index_rows) != 100 or test_units != list(range(1, 101)):
        failures.append({"reason": "CARDINALITY_OR_TEST_UNIT_SET", "rul": len(raw_lines), "index": len(index_rows), "test_units": test_units})
    for position, raw in enumerate(raw_lines, start=1):
        tokens = raw.split()
        try:
            value = int(tokens[0]) if len(tokens) == 1 else None
        except ValueError:
            value = None
        if value is None or value < 0:
            failures.append({"physical_line": position, "reason": "INVALID_RUL", "raw": raw.rstrip("\n")})
            continue
        if position <= len(index_rows):
            idx = index_rows[position - 1]
            expected_index = {
                "source_file": str(source.resolve()),
                "source_sha256": source_hash,
                "physical_line_number": str(position),
                "parsed_row_index": str(position - 1),
                "test_unit_id": str(position),
                "rul_value": str(value),
            }
            mismatches = {name: {"expected": expected, "actual": idx.get(name)} for name, expected in expected_index.items() if idx.get(name) != expected}
            if mismatches:
                failures.append({"physical_line": position, "reason": "INDEX_MISMATCH", "mismatches": mismatches})
    return gate("PASS" if not failures else "FAIL", len(raw_lines), failures, "line N -> Test Unit N; one nonnegative integer; every index field matched")


def main() -> int:
    train_gates, train_rows, train_units = validate_observations("train")
    test_gates, test_rows, test_units_map = validate_observations("test")
    test_units = sorted(test_units_map)
    rul_gate = validate_rul(test_units)
    combined: dict[str, Any] = {
        "policy": {"LOCAL_SOURCE_TRUST": "ACCEPTED_BY_STUDENT", "NASA_OFFICIAL_CHAIN_OF_CUSTODY": "NOT_REQUIRED_FOR_THIS_M2"},
        "checked": {"train_rows": len(train_rows), "test_rows": len(test_rows), "rul_rows": rul_gate["checked_records"]},
        "gates": {},
    }
    for name in ("SCHEMA_VALIDATION", "RAW_INDEX_VALIDATION", "UNIT_CYCLE_VALIDATION", "SETTINGS_VALIDATION", "SENSOR_VALIDATION"):
        failures = train_gates[name]["failures"] + test_gates[name]["failures"]
        combined["gates"][name] = {
            "status": "PASS" if train_gates[name]["status"] == test_gates[name]["status"] == "PASS" else "FAIL",
            "checked_records": train_gates[name]["checked_records"] + test_gates[name]["checked_records"],
            "failure_count": train_gates[name]["failure_count"] + test_gates[name]["failure_count"],
            "failures": failures[:20],
            "detail": train_gates[name]["detail"],
        }
    combined["gates"]["RUL_MAPPING_VALIDATION"] = rul_gate
    overall = all(item["status"] == "PASS" for item in combined["gates"].values())
    combined["overall"] = "PASS" if overall else "FAIL"
    print(json.dumps(combined, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
