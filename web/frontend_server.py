#!/usr/bin/env python3
"""Serve the FD001 frontend and proxy same-origin API reads to M3-A."""

from __future__ import annotations

import argparse
import http.client
import json
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class FrontendRequestHandler(SimpleHTTPRequestHandler):
    api_host: str
    api_port: int

    def log_message(self, format: str, *args: object) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def do_GET(self) -> None:
        if urlsplit(self.path).path.startswith("/api/"):
            self._proxy_api()
            return
        super().do_GET()

    def _proxy_api(self) -> None:
        connection = http.client.HTTPConnection(self.api_host, self.api_port, timeout=15)
        try:
            connection.request("GET", self.path, headers={"Accept": "application/json"})
            response = connection.getresponse()
            body = response.read()
        except (OSError, http.client.HTTPException):
            body = json.dumps(
                {
                    "error": {
                        "code": "CONNECTION_FAILURE",
                        "message": "The local FD001 API is unavailable",
                        "query": {},
                    }
                }
            ).encode("utf-8")
            self.send_response(HTTPStatus.BAD_GATEWAY)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        finally:
            connection.close()

        self.send_response(response.status)
        self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def create_frontend_server(
    static_dir: Path | str,
    host: str = "127.0.0.1",
    port: int = 8001,
    api_host: str = "127.0.0.1",
    api_port: int = 8000,
) -> ThreadingHTTPServer:
    handler = type(
        "BoundFrontendRequestHandler",
        (FrontendRequestHandler,),
        {"api_host": api_host, "api_port": api_port},
    )
    return ThreadingHTTPServer((host, port), partial(handler, directory=str(Path(static_dir))))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "localhost"])
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--api-host", default="127.0.0.1", choices=["127.0.0.1", "localhost"])
    parser.add_argument("--api-port", type=int, default=8000)
    args = parser.parse_args()
    static_dir = Path(__file__).resolve().parent / "frontend"
    server = create_frontend_server(static_dir, args.host, args.port, args.api_host, args.api_port)
    print(f"FD001 frontend listening on http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
