from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WEB_ROOT))

from frontend_server import create_frontend_server  # noqa: E402


class FakeAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        body = json.dumps({"path": self.path, "source": "TEST_ONLY"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FrontendServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        static_dir = Path(cls.temporary.name)
        (static_dir / "index.html").write_text("<!doctype html><title>FD001 test</title>", encoding="utf-8")

        cls.api = ThreadingHTTPServer(("127.0.0.1", 0), FakeAPIHandler)
        cls.api_thread = threading.Thread(target=cls.api.serve_forever, daemon=True)
        cls.api_thread.start()

        cls.frontend = create_frontend_server(
            static_dir,
            port=0,
            api_port=cls.api.server_port,
        )
        cls.frontend_thread = threading.Thread(target=cls.frontend.serve_forever, daemon=True)
        cls.frontend_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.frontend.shutdown()
        cls.frontend.server_close()
        cls.frontend_thread.join(timeout=5)
        cls.api.shutdown()
        cls.api.server_close()
        cls.api_thread.join(timeout=5)
        cls.temporary.cleanup()

    def request(self, path: str) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.frontend.server_port, timeout=10)
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, headers, body

    def test_static_frontend_is_served_with_security_headers(self) -> None:
        status, headers, body = self.request("/")
        self.assertEqual(200, status)
        self.assertIn(b"FD001 test", body)
        self.assertEqual("nosniff", headers["X-Content-Type-Options"])

    def test_api_path_and_query_are_proxied_same_origin(self) -> None:
        status, _, body = self.request("/api/history?split=train&unit=1")
        self.assertEqual(200, status)
        payload = json.loads(body)
        self.assertEqual("TEST_ONLY", payload["source"])
        self.assertEqual("/api/history?split=train&unit=1", payload["path"])

    def test_backend_connection_failure_is_safe_502(self) -> None:
        unavailable = create_frontend_server(Path(self.temporary.name), port=0, api_port=1)
        thread = threading.Thread(target=unavailable.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", unavailable.server_port, timeout=10)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            payload = json.loads(response.read())
            connection.close()
            self.assertEqual(502, response.status)
            self.assertEqual("CONNECTION_FAILURE", payload["error"]["code"])
            self.assertNotIn("/Users/", json.dumps(payload))
        finally:
            unavailable.shutdown()
            unavailable.server_close()
            thread.join(timeout=5)


class ProductionMarkupTestCase(unittest.TestCase):
    def test_evidence_panel_declares_every_required_contract_field(self) -> None:
        markup = (WEB_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        required = {
            "dataset_id",
            "source_type",
            "split",
            "unit_id",
            "sensor",
            "start_cycle",
            "end_cycle",
            "source_file",
            "source_sha256",
            "source_physical_line_1_based",
            "parsed_row_index_0_based",
        }
        for field in required:
            with self.subTest(field=field):
                self.assertIn(f'data-evidence="{field}"', markup)


if __name__ == "__main__":
    unittest.main()
