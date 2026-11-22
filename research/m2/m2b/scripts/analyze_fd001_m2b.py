#!/usr/bin/env python3
"""Reproducible, read-only FD001 M2-B quality and trend analysis."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[4]
M2A_MODULE_PATH = PROJECT_ROOT / "research" / "m2" / "m2a" / "scripts" / "verify_fd001_m2a.py"
NEAR_CONSTANT_NORMALIZED_RANGE_THRESHOLD = 1e-4
TREND_SLOPE_FLAT_TOLERANCE = 1e-12
TREND_CASES = {
    "train": {"unit_id": 1, "sensor_ids": [2, 3, 4]},
    "test": {"unit_id": 1, "sensor_ids": [2, 3, 4]},
}


def load_m2a_module():
    spec = importlib.util.spec_from_file_location("verify_fd001_m2a", M2A_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load M2-A module: {M2A_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def numeric_summary(values: Iterable[float]) -> dict[str, float | int]:
    materialized = list(values)
    if not materialized:
        raise ValueError("numeric summary requires at least one value")
    return {
        "min": min(materialized),
        "max": max(materialized),
        "mean": fmean(materialized),
        "population_stddev": pstdev(materialized),
        "unique_count": len(set(materialized)),
    }


def normalized_range(summary: dict[str, float | int]) -> float:
    minimum = float(summary["min"])
    maximum = float(summary["max"])
    return (maximum - minimum) / max(abs(minimum), abs(maximum), 1.0)


def quality_summary(split_result: dict[str, Any]) -> dict[str, Any]:
    rows = split_result["rows"]
    keys = [(row["unit_id"], row["cycle"]) for row in rows]
    duplicate_keys = sum(count - 1 for count in Counter(keys).values() if count > 1)
    cycles_by_unit: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        cycles_by_unit[row["unit_id"]].append(row["cycle"])

    missing_cycles = 0
    invalid_cycles = 0
    for cycles in cycles_by_unit.values():
        invalid_cycles += sum(1 for cycle in cycles if not isinstance(cycle, int) or cycle <= 0)
        if cycles:
            expected = set(range(1, max(cycles) + 1))
            missing_cycles += len(expected.difference(cycles))

    sensor_summaries: dict[str, dict[str, Any]] = {}
    constant_sensors: list[str] = []
    near_constant_sensors: list[str] = []
    for index in range(21):
        name = f"sensor_{index + 1}"
        summary = numeric_summary(row["sensors"][index] for row in rows)
        summary["normalized_range"] = normalized_range(summary)
        is_constant = summary["unique_count"] == 1
        is_near_constant = (
            not is_constant
            and float(summary["normalized_range"]) <= NEAR_CONSTANT_NORMALIZED_RANGE_THRESHOLD
        )
        summary["constant"] = is_constant
        summary["near_constant"] = is_near_constant
        sensor_summaries[name] = summary
        if is_constant:
            constant_sensors.append(name)
        if is_near_constant:
            near_constant_sensors.append(name)

    setting_summaries = {
        f"setting_{index + 1}": numeric_summary(row["settings"][index] for row in rows)
        for index in range(3)
    }

    non_finite = 0
    for row in rows:
        non_finite += sum(not math.isfinite(float(value)) for value in row["settings"] + row["sensors"])

    return {
        "split": split_result["split"].upper(),
        "source_file": Path(split_result["path"]).name,
        "source_sha256": split_result["sha256"],
        "observation_count": len(rows),
        "unit_count": len(cycles_by_unit),
        "cycle_range": [min(row["cycle"] for row in rows), max(row["cycle"] for row in rows)],
        "missing_values": split_result["missing_values"],
        "non_finite_values": non_finite,
        "duplicate_unit_cycle_keys": duplicate_keys,
        "invalid_cycle_values": invalid_cycles,
        "missing_cycles_within_unit_1_to_max": missing_cycles,
        "parsing_anomalies": split_result["physical_line_count"] - len(rows),
        "constant_sensors": constant_sensors,
        "near_constant_sensors": near_constant_sensors,
        "near_constant_definition": (
            "non-constant sensor with (max-min)/max(abs(min),abs(max),1) <= "
            f"{NEAR_CONSTANT_NORMALIZED_RANGE_THRESHOLD:g}"
        ),
        "statistics_method": (
            "mean is arithmetic mean over all observations in the split; "
            "population_stddev uses denominator N; unique_count uses exact parsed float values"
        ),
        "sensor_statistics": sensor_summaries,
        "operational_setting_statistics": setting_summaries,
    }


def linear_slope(cycles: list[int], values: list[float]) -> float:
    if len(cycles) != len(values) or len(cycles) < 2:
        raise ValueError("linear slope requires aligned sequences with at least two observations")
    x_mean = fmean(cycles)
    y_mean = fmean(values)
    denominator = math.fsum((cycle - x_mean) ** 2 for cycle in cycles)
    if denominator == 0:
        raise ValueError("linear slope is undefined for a zero-width cycle range")
    numerator = math.fsum((cycle - x_mean) * (value - y_mean) for cycle, value in zip(cycles, values))
    return numerator / denominator


def trend_case(split_result: dict[str, Any], unit_id: int, sensor_id: int) -> dict[str, Any]:
    if not 1 <= sensor_id <= 21:
        raise ValueError(f"invalid sensor_id: {sensor_id}")
    rows = [row for row in split_result["rows"] if row["unit_id"] == unit_id]
    if not rows:
        raise ValueError(f"unit not found in {split_result['split']}: {unit_id}")
    rows.sort(key=lambda row: row["cycle"])
    cycles = [row["cycle"] for row in rows]
    values = [row["sensors"][sensor_id - 1] for row in rows]
    summary = numeric_summary(values)
    slope = linear_slope(cycles, values)
    if abs(slope) <= TREND_SLOPE_FLAT_TOLERANCE:
        direction = "FLAT"
    elif slope > 0:
        direction = "INCREASING"
    else:
        direction = "DECREASING"
    return {
        "split": split_result["split"].upper(),
        "source_file": Path(split_result["path"]).name,
        "source_sha256": split_result["sha256"],
        "source_physical_line_start_1_based": rows[0]["physical_line_number"],
        "source_physical_line_end_1_based": rows[-1]["physical_line_number"],
        "parsed_row_index_start_0_based": rows[0]["parsed_row_index"],
        "parsed_row_index_end_0_based": rows[-1]["parsed_row_index"],
        "unit_id": unit_id,
        "sensor_id": sensor_id,
        "cycle_range": [cycles[0], cycles[-1]],
        "observation_count": len(rows),
        "first_value": values[0],
        "last_value": values[-1],
        "minimum": summary["min"],
        "maximum": summary["max"],
        "mean": summary["mean"],
        "delta_last_minus_first": values[-1] - values[0],
        "linear_slope": slope,
        "slope_unit": "recorded sensor-value units per cycle; physical sensor unit is not defined by this contract",
        "trend_direction": direction,
        "trend_method": (
            "ordinary least-squares slope with cycle as x and parsed sensor value as y; "
            f"abs(slope) <= {TREND_SLOPE_FLAT_TOLERANCE:g} is FLAT"
        ),
    }


def build_analysis(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    m2a = load_m2a_module()
    verified = m2a.verify_all(project_root)
    quality = {split: quality_summary(verified[split]) for split in ("train", "test")}
    trends = []
    for split, selection in TREND_CASES.items():
        for sensor_id in selection["sensor_ids"]:
            trends.append(trend_case(verified[split], selection["unit_id"], sensor_id))
    rul = verified["rul"]
    return {
        "work_item_id": "WO-M2-RESEARCH-001-B",
        "dataset_id": "NASA_CMAPSS_FD001",
        "source_type": "NASA_FD001_LOCAL_TRUSTED",
        "simulation_disclosure": (
            "NASA C-MAPSS simulated turbofan degradation data; not physical engine field measurements"
        ),
        "source_sha256": {
            "train_FD001.txt": verified["train"]["sha256"],
            "test_FD001.txt": verified["test"]["sha256"],
            "RUL_FD001.txt": rul["sha256"],
        },
        "quality": quality,
        "trend_cases": trends,
        "rul_mapping": {
            "rule": rul["mapping_rule"],
            "label_semantics": "rul_at_last_observed_cycle for each Test unit",
            "is_sensor_observation": False,
            "test_final_observation_is_failure": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    try:
        result = build_analysis()
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
