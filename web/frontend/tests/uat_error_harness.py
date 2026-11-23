#!/usr/bin/env python3
"""TEST_ONLY Browser UAT harness for frontend error-state classification."""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WEB_ROOT))

from frontend_server import create_frontend_server  # noqa: E402


ERRORS = {
    400: ("INVALID_QUERY_VALUE", "TEST_ONLY query validation error"),
    404: ("OBSERVATION_NOT_FOUND", "TEST_ONLY observation not found"),
    503: ("SOURCE_NOT_VALIDATED", "TEST_ONLY source not validated"),
}


def error_handler(status: int) -> type[BaseHTTPRequestHandler]:
    class ErrorHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            code, message = ERRORS[status]
            body = json.dumps({"error": {"code": code, "message": message, "query": {}}}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ErrorHandler


def main() -> None:
    static_dir = WEB_ROOT / "frontend"
    servers: list[ThreadingHTTPServer] = []
    threads: list[threading.Thread] = []
    for status, api_port, frontend_port in ((400, 8010, 8011), (404, 8012, 8013), (503, 8014, 8015)):
        api = ThreadingHTTPServer(("127.0.0.1", api_port), error_handler(status))
        frontend = create_frontend_server(static_dir, port=frontend_port, api_port=api_port)
        servers.extend((api, frontend))
    servers.append(create_frontend_server(static_dir, port=8017, api_port=1))

    for server in servers:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        threads.append(thread)
    print("TEST_ONLY UAT error frontends: 400=8011 404=8013 503=8015 connection=8017")
    try:
        threads[0].join()
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
