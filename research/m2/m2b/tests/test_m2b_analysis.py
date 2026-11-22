#!/usr/bin/env python3
"""M2-B data-quality and trend reproducibility tests."""

from __future__ import annotations

import importlib.util
import math
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = PROJECT_ROOT / "research" / "m2" / "m2b" / "scripts" / "analyze_fd001_m2b.py"
SPEC = importlib.util.spec_from_file_location("analyze_fd001_m2b", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class M2BAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = MODULE.build_analysis(PROJECT_ROOT)

    def test_source_integrity_and_split_counts(self) -> None:
        self.assertEqual(
            self.result["source_sha256"],
            {
                "train_FD001.txt": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
                "test_FD001.txt": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
                "RUL_FD001.txt": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
            },
        )
        self.assertEqual(self.result["quality"]["train"]["observation_count"], 20631)
        self.assertEqual(self.result["quality"]["test"]["observation_count"], 13096)

    def test_quality_integrity_counts(self) -> None:
        for split in ("train", "test"):
            quality = self.result["quality"][split]
            self.assertEqual(quality["unit_count"], 100)
            self.assertEqual(quality["missing_values"], 0)
            self.assertEqual(quality["non_finite_values"], 0)
            self.assertEqual(quality["duplicate_unit_cycle_keys"], 0)
            self.assertEqual(quality["invalid_cycle_values"], 0)
            self.assertEqual(quality["missing_cycles_within_unit_1_to_max"], 0)
            self.assertEqual(quality["parsing_anomalies"], 0)
            self.assertEqual(len(quality["sensor_statistics"]), 21)
            self.assertEqual(len(quality["operational_setting_statistics"]), 3)

    def test_sensor_statistics_are_self_consistent(self) -> None:
        for split in ("train", "test"):
            for summary in self.result["quality"][split]["sensor_statistics"].values():
                self.assertLessEqual(summary["min"], summary["mean"])
                self.assertLessEqual(summary["mean"], summary["max"])
                self.assertGreaterEqual(summary["population_stddev"], 0)
                self.assertGreaterEqual(summary["unique_count"], 1)
                self.assertTrue(math.isfinite(summary["normalized_range"]))

    def test_trend_cases_are_traceable_and_variable(self) -> None:
        self.assertEqual(len(self.result["trend_cases"]), 6)
        self.assertEqual({case["split"] for case in self.result["trend_cases"]}, {"TRAIN", "TEST"})
        self.assertEqual({case["sensor_id"] for case in self.result["trend_cases"]}, {2, 3, 4})
        for case in self.result["trend_cases"]:
            self.assertLess(case["source_physical_line_start_1_based"], case["source_physical_line_end_1_based"])
            self.assertLess(case["parsed_row_index_start_0_based"], case["parsed_row_index_end_0_based"])
            self.assertGreater(case["maximum"], case["minimum"])
            self.assertTrue(math.isfinite(case["linear_slope"]))
            self.assertIn(case["trend_direction"], {"INCREASING", "DECREASING", "FLAT"})

    def test_trend_reproducibility(self) -> None:
        rerun = MODULE.build_analysis(PROJECT_ROOT)
        self.assertEqual(self.result["trend_cases"], rerun["trend_cases"])

    def test_rul_semantics(self) -> None:
        mapping = self.result["rul_mapping"]
        self.assertEqual(mapping["label_semantics"], "rul_at_last_observed_cycle for each Test unit")
        self.assertFalse(mapping["is_sensor_observation"])
        self.assertFalse(mapping["test_final_observation_is_failure"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
