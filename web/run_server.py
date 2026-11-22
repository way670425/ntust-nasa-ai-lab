#!/usr/bin/env python3
"""Start the local-only FD001 read-only API."""

from __future__ import annotations

import argparse
from pathlib import Path

from fd001_api import create_server


def main() -> None:
    default_data = Path(__file__).resolve().parents[1] / "data" / "FD001"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data)
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "localhost"])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = create_server(args.data_dir, args.host, args.port)
    print(f"FD001 read-only API listening on http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
