#!/usr/bin/env python3
"""Read-only FD001 M2-A verifier and traceable raw-index generator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any


DATASET_ID = "NASA_CMAPSS_FD001"
COLUMNS = ["unit_id", "cycle", "setting_1", "setting_2", "setting_3"] + [f"sensor_{i}" for i in range(1, 22)]
EXPECTED_HASHES = {
    "train": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "test": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
    "rul": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_observations(path: Path, split: str, expected_hash: str) -> dict[str, Any]:
    actual_hash = sha256(path)
    if actual_hash != expected_hash:
        raise ValueError(f"FILE_HASH_MISMATCH: {path} expected={expected_hash} actual={actual_hash}")

    rows: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    physical_lines = 0
    with path.open("r", encoding="ascii", newline="") as handle:
        for physical_line, raw_line in enumerate(handle, start=1):
            physical_lines += 1
            tokens = raw_line.split()
            if len(tokens) != 26:
                invalid.append({"physical_line": physical_line, "reason": "COLUMN_COUNT", "actual": len(tokens)})
                continue
            try:
                unit_id = int(tokens[0])
                cycle = int(tokens[1])
                numeric = [float(value) for value in tokens[2:]]
                if any(not math.isfinite(value) for value in numeric):
                    raise ValueError("non-finite")
            except ValueError as exc:
                invalid.append({"physical_line": physical_line, "reason": "INVALID_NUMERIC", "detail": str(exc)})
                continue
            rows.append(
                {
                    "physical_line_number": physical_line,
                    "parsed_row_index": len(rows),
                    "unit_id": unit_id,
                    "cycle": cycle,
                    "settings": numeric[:3],
                    "sensors": numeric[3:],
                    "tokens": tokens,
                }
            )

    if invalid:
        raise ValueError(f"RAW_SCHEMA_MISMATCH: {path} invalid={invalid[:5]}")
    if len(rows) != physical_lines:
        raise ValueError(f"RAW_SCHEMA_MISMATCH: parsed={len(rows)} physical={physical_lines}")

    by_unit: dict[int, list[int]] = defaultdict(list)
    keys: set[tuple[int, int]] = set()
    duplicate_keys: list[tuple[int, int]] = []
    for row in rows:
        key = (row["unit_id"], row["cycle"])
        if key in keys:
            duplicate_keys.append(key)
        keys.add(key)
        by_unit[row["unit_id"]].append(row["cycle"])

    sequence_failures = {}
    for unit_id, cycles in by_unit.items():
        expected = list(range(1, len(cycles) + 1))
        if cycles != expected:
            sequence_failures[unit_id] = {"observed_first": cycles[:5], "observed_last": cycles[-5:]}

    if duplicate_keys or sequence_failures:
        raise ValueError(
            f"UNIT_CYCLE_INTEGRITY_FAILURE: duplicate_keys={duplicate_keys[:5]} sequence_units={list(sequence_failures)[:5]}"
        )

    settings = list(zip(*(row["settings"] for row in rows)))
    setting_summary = {
        f"setting_{index}": {
            "min": min(values),
            "max": max(values),
            "mean": fmean(values),
            "unique_count": len(set(values)),
        }
        for index, values in enumerate(settings, start=1)
    }

    units = sorted(by_unit)
    cycle_max_by_unit = {str(unit): by_unit[unit][-1] for unit in units}
    return {
        "split": split,
        "path": str(path.resolve()),
        "sha256": actual_hash,
        "physical_line_count": physical_lines,
        "parsed_row_count": len(rows),
        "effective_column_count": 26,
        "unit_count": len(units),
        "unit_id_min": min(units),
        "unit_id_max": max(units),
        "cycle_min": min(row["cycle"] for row in rows),
        "cycle_max": max(row["cycle"] for row in rows),
        "unit_cycle_sequences": "CONTIGUOUS_1_BASED_IN_SOURCE_ORDER",
        "duplicate_unit_cycle_keys": len(duplicate_keys),
        "missing_values": 0,
        "invalid_values": 0,
        "operational_setting_count": 3,
        "sensor_count": 21,
        "setting_summary": setting_summary,
        "cycle_max_by_unit": cycle_max_by_unit,
        "first_source_row": {"physical_line": 1, "tokens": rows[0]["tokens"]},
        "last_source_row": {"physical_line": physical_lines, "tokens": rows[-1]["tokens"]},
        "rows": rows,
    }


def parse_rul(path: Path, expected_hash: str, expected_test_units: list[int]) -> dict[str, Any]:
    actual_hash = sha256(path)
    if actual_hash != expected_hash:
        raise ValueError(f"FILE_HASH_MISMATCH: {path} expected={expected_hash} actual={actual_hash}")
    rows = []
    with path.open("r", encoding="ascii", newline="") as handle:
        for physical_line, raw_line in enumerate(handle, start=1):
            tokens = raw_line.split()
            if len(tokens) != 1:
                raise ValueError(f"RAW_SCHEMA_MISMATCH: RUL line={physical_line} fields={len(tokens)}")
            try:
                value = int(tokens[0])
            except ValueError as exc:
                raise ValueError(f"RAW_SCHEMA_MISMATCH: RUL line={physical_line} value={tokens[0]!r}") from exc
            if value < 0:
                raise ValueError(f"RUL_ALIGNMENT_FAILURE: negative RUL line={physical_line} value={value}")
            rows.append(
                {
                    "physical_line_number": physical_line,
                    "parsed_row_index": physical_line - 1,
                    "test_unit_id": physical_line,
                    "rul_value": value,
                }
            )
    mapped_units = [row["test_unit_id"] for row in rows]
    if mapped_units != expected_test_units:
        raise ValueError(f"RUL_ALIGNMENT_FAILURE: mapped_units={mapped_units[:5]}... count={len(mapped_units)}")
    return {
        "path": str(path.resolve()),
        "sha256": actual_hash,
        "physical_line_count": len(rows),
        "parsed_row_count": len(rows),
        "effective_column_count": 1,
        "mapping_rule": "RUL physical line N (1-based) maps to test unit_id N",
        "test_unit_count": len(expected_test_units),
        "complete_mapping": True,
        "nonnegative_values": True,
        "rul_min": min(row["rul_value"] for row in rows),
        "rul_max": max(row["rul_value"] for row in rows),
        "first_source_row": rows[0],
        "last_source_row": rows[-1],
        "rows": rows,
    }


def verify_all(project_root: Path) -> dict[str, Any]:
    data_dir = project_root / "data" / "FD001"
    train = parse_observations(data_dir / "train_FD001.txt", "train", EXPECTED_HASHES["train"])
    test = parse_observations(data_dir / "test_FD001.txt", "test", EXPECTED_HASHES["test"])
    test_units = sorted({row["unit_id"] for row in test["rows"]})
    rul = parse_rul(data_dir / "RUL_FD001.txt", EXPECTED_HASHES["rul"], test_units)
    return {
        "dataset_id": DATASET_ID,
        "source_acceptance": "STUDENT_ACCEPTED_LOCAL_SOURCE_WITHOUT_OFFICIAL_CHAIN_OF_CUSTODY",
        "source_row_convention": "physical_line_number is 1-based; parsed_row_index is 0-based",
        "train_semantics": "complete run-to-failure observation trajectories (dataset documentation semantics)",
        "test_semantics": "truncated before failure; final observation is not a failure point",
        "rul_semantics": "one label per test unit; not a sensor observation and not joined per sensor row",
        "columns": COLUMNS,
        "train": train,
        "test": test,
        "rul": rul,
    }


def open_new(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("x", encoding="utf-8", newline="")


def write_observation_index(result: dict[str, Any], output_path: Path) -> None:
    with open_new(output_path) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset_id",
                "split",
                "source_file",
                "source_sha256",
                "physical_line_number",
                "parsed_row_index",
                "unit_id",
                "cycle",
            ],
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow(
                {
                    "dataset_id": DATASET_ID,
                    "split": result["split"],
                    "source_file": result["path"],
                    "source_sha256": result["sha256"],
                    "physical_line_number": row["physical_line_number"],
                    "parsed_row_index": row["parsed_row_index"],
                    "unit_id": row["unit_id"],
                    "cycle": row["cycle"],
                }
            )


def write_rul_index(result: dict[str, Any], output_path: Path) -> None:
    with open_new(output_path) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_file",
                "source_sha256",
                "physical_line_number",
                "parsed_row_index",
                "test_unit_id",
                "rul_value",
            ],
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({"source_file": result["path"], "source_sha256": result["sha256"], **row})


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    summary = {key: value for key, value in result.items() if key not in {"train", "test", "rul"}}
    for split in ("train", "test", "rul"):
        summary[split] = {key: value for key, value in result[split].items() if key != "rows"}
    return summary


def main() -> int:
    project_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "research" / "m2" / "m2a" / "output")
    args = parser.parse_args()
    try:
        result = verify_all(project_root)
        write_observation_index(result["train"], args.output_dir / "train_raw_index.csv")
        write_observation_index(result["test"], args.output_dir / "test_raw_index.csv")
        write_rul_index(result["rul"], args.output_dir / "rul_raw_index.csv")
        summary = public_summary(result)
        with open_new(args.output_dir / "m2a_summary.json") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "PASS_CANDIDATE", **summary}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
