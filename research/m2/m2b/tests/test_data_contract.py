#!/usr/bin/env python3
"""Static validation for the published FD001 data contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = PROJECT_ROOT / "research" / "m2" / "data_contract.md"


class DataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_dataset_identity_and_splits(self) -> None:
        for required in (
            "NASA_CMAPSS_FD001",
            "NASA_FD001_LOCAL_TRUSTED",
            "TRAIN",
            "TEST",
            "TEST_RUL",
            "rul_at_last_observed_cycle",
        ):
            self.assertIn(required, self.text)

    def test_schema_and_traceability_fields(self) -> None:
        for required in (
            "source_file",
            "source_sha256",
            "source_physical_line_1_based",
            "parsed_row_index_0_based",
            "unit_id",
            "cycle",
            "setting_1",
            "sensor_21",
        ):
            self.assertIn(required, self.text)
        sensor_fields = re.findall(
            r"^\| `(sensor_(?:2[01]|1[0-9]|[1-9]))` \| number \|",
            self.text,
            flags=re.MULTILINE,
        )
        expected_sensor_fields = {f"sensor_{index}" for index in range(1, 22)}
        self.assertEqual(len(sensor_fields), 21)
        self.assertEqual(len(set(sensor_fields)), 21)
        self.assertEqual(set(sensor_fields), expected_sensor_fields)
        self.assertNotIn("operating_setting", sensor_fields)

    def test_safety_semantics(self) -> None:
        for required in (
            "NASA C-MAPSS FD001 是模擬引擎退化資料集",
            "學生已信任的本地 FD001 檔案",
            "模擬資料不等於實體引擎現場量測",
            "不得聲稱未經證實的設備故障或 RUL 預測",
            "不是 Sensor Observation",
            "不得視為故障時刻",
            "不是實體設備實測資料",
            "不實作 Web API",
        ):
            self.assertIn(required, self.text)

    def test_no_private_absolute_path(self) -> None:
        self.assertNotIn("/Users/", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
