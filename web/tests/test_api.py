from __future__ import annotations

import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEB_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data" / "FD001"
sys.path.insert(0, str(WEB_ROOT))

from fd001_api.app import create_server  # noqa: E402
from fd001_api.loader import EXPECTED_HASHES, FD001Dataset  # noqa: E402


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(DATA_DIR, port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, method: str, path: str) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request(method, path)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def assert_error(self, path: str, status: int, code: str) -> None:
        actual_status, payload = self.request("GET", path)
        self.assertEqual(status, actual_status)
        self.assertEqual(code, payload["error"]["code"])
        self.assertNotIn(str(PROJECT_ROOT), json.dumps(payload))

    def test_health(self) -> None:
        status, payload = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["data_validated"])
        self.assertTrue(payload["read_only"])

    def test_catalog(self) -> None:
        status, payload = self.request("GET", "/api/catalog")
        self.assertEqual(200, status)
        self.assertEqual(
            {
                "dataset_id",
                "source_type",
                "available_splits",
                "observation_schema",
                "operating_settings",
                "sensor_names",
                "sensor_units",
                "source_provenance",
            },
            set(payload),
        )
        self.assertEqual(["TRAIN", "TEST"], payload["available_splits"])
        self.assertEqual(3, len(payload["operating_settings"]))
        self.assertEqual(21, len(payload["sensor_names"]))
        self.assertIn("not a Sensor History Split", payload["source_provenance"]["test_rul"])

    def test_catalog_has_complete_ordered_observation_schema(self) -> None:
        status, payload = self.request("GET", "/api/catalog")
        self.assertEqual(200, status)
        schema = payload["observation_schema"]
        expected_names = (
            ["unit_id", "cycle"]
            + [f"setting_{number}" for number in range(1, 4)]
            + [f"sensor_{number}" for number in range(1, 22)]
        )
        self.assertEqual(26, len(schema))
        self.assertEqual(expected_names, [field["name"] for field in schema])
        self.assertEqual(list(range(1, 27)), [field["source_column_position"] for field in schema])
        self.assertEqual(
            ["integer", "integer"] + ["number"] * 24,
            [field["data_type"] for field in schema],
        )
        for field in schema:
            self.assertEqual(
                {"name", "data_type", "nullable", "source_column_position", "query_semantics"},
                set(field),
            )
            self.assertIs(field["nullable"], False)
            self.assertTrue(field["query_semantics"].strip())
        self.assertIn("split-scoped", schema[0]["query_semantics"])
        self.assertIn("beginning at 1", schema[1]["query_semantics"])
        self.assertTrue(all("source-defined or unspecified" in field["query_semantics"] for field in schema[2:]))

    def test_units_are_split_scoped_and_source_derived(self) -> None:
        train_status, train = self.request("GET", "/api/units?split=train")
        test_status, test = self.request("GET", "/api/units?split=test")
        self.assertEqual((200, 200), (train_status, test_status))
        self.assertEqual("TRAIN", train["split"])
        self.assertEqual("TEST", test["split"])
        self.assertEqual(
            {"unit_id": 1, "min_cycle": 1, "max_cycle": 192, "observation_count": 192},
            train["units"][0],
        )
        self.assertEqual(
            {"unit_id": 1, "min_cycle": 1, "max_cycle": 31, "observation_count": 31},
            test["units"][0],
        )
        self.assertEqual(100, len(train["units"]))
        self.assertEqual(100, len(test["units"]))

    def test_history_train_unit_1_sensor_7_cycles_1_to_20(self) -> None:
        status, payload = self.request(
            "GET", "/api/history?split=train&unit=1&sensor=7&start=1&end=20"
        )
        self.assertEqual(200, status)
        self.assertEqual(20, payload["observation_count"])

        independently_parsed = []
        with (DATA_DIR / "train_FD001.txt").open("r", encoding="utf-8") as source:
            for physical_line, line in enumerate(source, start=1):
                fields = line.split()
                if int(fields[0]) == 1 and 1 <= int(fields[1]) <= 20:
                    independently_parsed.append(
                        (int(fields[1]), float(fields[11]), physical_line, physical_line - 1)
                    )

        self.assertEqual(20, len(independently_parsed))
        for observation, expected in zip(payload["observations"], independently_parsed):
            cycle, value, physical_line, parsed_index = expected
            self.assertEqual(cycle, observation["cycle"])
            self.assertEqual("sensor_7", observation["sensor"])
            self.assertEqual(value, observation["value"])
            evidence = observation["source_evidence"]
            self.assertEqual("train_FD001.txt", evidence["source_file"])
            self.assertEqual(EXPECTED_HASHES["train_FD001.txt"], evidence["source_sha256"])
            self.assertEqual(physical_line, evidence["source_physical_line_1_based"])
            self.assertEqual(parsed_index, evidence["parsed_row_index_0_based"])
        self.assertEqual(1, payload["observations"][0]["source_evidence"]["source_physical_line_1_based"])

    def test_test_unit_1_query(self) -> None:
        status, payload = self.request(
            "GET", "/api/history?split=test&unit=1&sensor=7&start=1&end=2"
        )
        self.assertEqual(200, status)
        self.assertEqual("TEST", payload["split"])
        self.assertEqual([1, 2], [row["cycle"] for row in payload["observations"]])

    def test_negative_queries(self) -> None:
        cases = [
            ("/api/units", 400, "INVALID_QUERY_VALUE"),
            ("/api/units?split=invalid", 400, "INVALID_SPLIT"),
            ("/api/history?split=train&unit=999&sensor=7&start=1&end=2", 404, "OBSERVATION_NOT_FOUND"),
            ("/api/history?split=train&unit=1&sensor=7&start=999&end=999", 404, "OBSERVATION_NOT_FOUND"),
            ("/api/history?split=train&unit=1&sensor=22&start=1&end=2", 400, "INVALID_SENSOR"),
            ("/api/history?split=bad&unit=1&sensor=7&start=1&end=2", 400, "INVALID_SPLIT"),
            ("/api/history?split=train&unit=1&sensor=7&start=2&end=1", 400, "INVALID_QUERY_VALUE"),
            ("/api/history?split=train&unit=x&sensor=7&start=1&end=2", 400, "INVALID_QUERY_VALUE"),
            ("/api/history?split=train&unit=1&sensor=7&start=x&end=2", 400, "INVALID_QUERY_VALUE"),
            ("/api/history?split=train&unit=1&sensor=7&start=1", 400, "INVALID_QUERY_VALUE"),
        ]
        for path, status, code in cases:
            with self.subTest(path=path):
                self.assert_error(path, status, code)

    def test_strict_query_parameter_validation(self) -> None:
        cases = [
            "/api/health?foo=1",
            "/api/catalog?foo=1",
            "/api/units?split=train&foo=1",
            "/api/history?split=train&unit=1&sensor=7&start=1&end=20&foo=1",
            "/api/units?split=train&split=test",
            "/api/history?split=train&unit=1&unit=2&sensor=7&start=1&end=20",
            "/api/units",
            "/api/history?split=train&unit=1",
        ]
        for path in cases:
            with self.subTest(path=path):
                self.assert_error(path, 400, "INVALID_QUERY_VALUE")

    def test_invalid_sensor_contract(self) -> None:
        cases = [
            ("abc", "INVALID_QUERY_VALUE"),
            ("sensor_7", "INVALID_QUERY_VALUE"),
            ("0", "INVALID_SENSOR"),
            ("22", "INVALID_SENSOR"),
            ("-1", "INVALID_SENSOR"),
            ("7.5", "INVALID_QUERY_VALUE"),
            ("", "INVALID_QUERY_VALUE"),
        ]
        for sensor, code in cases:
            path = f"/api/history?split=train&unit=1&sensor={sensor}&start=1&end=20"
            with self.subTest(sensor=sensor):
                self.assert_error(path, 400, code)

        status, payload = self.request(
            "GET", "/api/history?split=train&unit=1&sensor=7&start=1&end=20"
        )
        self.assertEqual(200, status)
        self.assertEqual(20, payload["observation_count"])

    def test_write_methods_are_forbidden(self) -> None:
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                status, payload = self.request(method, "/api/data")
                self.assertEqual(405, status)
                self.assertEqual("METHOD_NOT_ALLOWED", payload["error"]["code"])


class SourceFailureTestCase(unittest.TestCase):
    def _copy_sources(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        target = Path(temporary.name)
        for filename in EXPECTED_HASHES:
            shutil.copyfile(DATA_DIR / filename, target / filename)
        return temporary, target

    def test_missing_source_is_not_validated_and_hides_private_path(self) -> None:
        temporary, target = self._copy_sources()
        self.addCleanup(temporary.cleanup)
        (target / "test_FD001.txt").unlink()
        dataset = FD001Dataset(target)
        self.assertFalse(dataset.validated)
        self.assertNotIn(str(target), dataset.validation_error or "")

    def test_missing_source_health_is_503_and_hides_private_path(self) -> None:
        temporary, target = self._copy_sources()
        self.addCleanup(temporary.cleanup)
        (target / "test_FD001.txt").unlink()
        server = create_server(target, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            payload = json.loads(response.read())
            connection.close()
            self.assertEqual(503, response.status)
            self.assertEqual("SOURCE_NOT_VALIDATED", payload["error"]["code"])
            self.assertNotIn(str(target), json.dumps(payload))
            self.assertNotIn("data_validated", payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_hash_mismatch_is_not_validated(self) -> None:
        temporary, target = self._copy_sources()
        self.addCleanup(temporary.cleanup)
        with (target / "train_FD001.txt").open("ab") as source:
            source.write(b"tamper")
        dataset = FD001Dataset(target)
        self.assertFalse(dataset.validated)
        self.assertIn("SHA-256", dataset.validation_error or "")

    def test_missing_sensor_value_and_non_finite_value_are_rejected(self) -> None:
        for replacement in ("", "nan"):
            with self.subTest(replacement=replacement):
                temporary, target = self._copy_sources()
                self.addCleanup(temporary.cleanup)
                train = target / "train_FD001.txt"
                lines = train.read_text(encoding="utf-8").splitlines()
                fields = lines[0].split()
                if replacement:
                    fields[11] = replacement
                else:
                    fields.pop(11)
                lines[0] = " ".join(fields)
                train.write_text("\n".join(lines) + "\n", encoding="utf-8")
                # Override only the test copy's expected hash so schema/finite validation is exercised.
                from fd001_api import loader

                original = loader.EXPECTED_HASHES["train_FD001.txt"]
                loader.EXPECTED_HASHES["train_FD001.txt"] = loader._file_sha256(train)
                try:
                    dataset = FD001Dataset(target)
                finally:
                    loader.EXPECTED_HASHES["train_FD001.txt"] = original
                self.assertFalse(dataset.validated)
                self.assertTrue(
                    "field count" in (dataset.validation_error or "")
                    or "non-finite" in (dataset.validation_error or "")
                )


if __name__ == "__main__":
    unittest.main()
