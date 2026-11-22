#!/usr/bin/env python3
"""M2-A tests against the student-accepted local FD001 files."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = PROJECT_ROOT / "research" / "m2" / "m2a" / "scripts" / "verify_fd001_m2a.py"
SPEC = importlib.util.spec_from_file_location("verify_fd001_m2a", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FD001M2ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = MODULE.verify_all(PROJECT_ROOT)

    def test_hashes_and_row_counts(self) -> None:
        self.assertEqual(self.result["train"]["sha256"], MODULE.EXPECTED_HASHES["train"])
        self.assertEqual(self.result["test"]["sha256"], MODULE.EXPECTED_HASHES["test"])
        self.assertEqual(self.result["rul"]["sha256"], MODULE.EXPECTED_HASHES["rul"])
        self.assertEqual(self.result["train"]["physical_line_count"], 20631)
        self.assertEqual(self.result["test"]["physical_line_count"], 13096)
        self.assertEqual(self.result["rul"]["physical_line_count"], 100)

    def test_observation_schema(self) -> None:
        for split in ("train", "test"):
            observed = self.result[split]
            self.assertEqual(observed["effective_column_count"], 26)
            self.assertEqual(observed["operational_setting_count"], 3)
            self.assertEqual(observed["sensor_count"], 21)
            self.assertEqual(observed["missing_values"], 0)
            self.assertEqual(observed["invalid_values"], 0)

    def test_units_and_cycle_integrity(self) -> None:
        for split in ("train", "test"):
            observed = self.result[split]
            self.assertEqual(observed["unit_count"], 100)
            self.assertEqual((observed["unit_id_min"], observed["unit_id_max"]), (1, 100))
            self.assertEqual(observed["duplicate_unit_cycle_keys"], 0)
            self.assertEqual(observed["unit_cycle_sequences"], "CONTIGUOUS_1_BASED_IN_SOURCE_ORDER")

    def test_rul_alignment(self) -> None:
        rul = self.result["rul"]
        self.assertEqual(rul["test_unit_count"], 100)
        self.assertTrue(rul["complete_mapping"])
        self.assertTrue(rul["nonnegative_values"])
        self.assertEqual(rul["first_source_row"], {"physical_line_number": 1, "parsed_row_index": 0, "test_unit_id": 1, "rul_value": 112})
        self.assertEqual(rul["last_source_row"], {"physical_line_number": 100, "parsed_row_index": 99, "test_unit_id": 100, "rul_value": 20})

    def test_source_row_conventions_and_excerpts(self) -> None:
        self.assertIn("1-based", self.result["source_row_convention"])
        self.assertIn("0-based", self.result["source_row_convention"])
        self.assertEqual(self.result["train"]["first_source_row"]["tokens"][:5], ["1", "1", "-0.0007", "-0.0004", "100.0"])
        self.assertEqual(self.result["test"]["first_source_row"]["tokens"][:5], ["1", "1", "0.0023", "0.0003", "100.0"])

    def test_test_semantics_do_not_mark_last_row_as_failure(self) -> None:
        self.assertIn("not a failure point", self.result["test_semantics"])
        self.assertIn("not a sensor observation", self.result["rul_semantics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
