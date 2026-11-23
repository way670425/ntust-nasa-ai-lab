#!/usr/bin/env python3
"""M5 read-only checks against the real accepted FD001 API."""

from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import urlopen

BASE = "http://127.0.0.1:8000"
CASES = [
    ("INVALID_SPLIT", "/api/units?split=invalid", 400, "INVALID_SPLIT"),
    ("INVALID_UNIT", "/api/history?split=train&unit=0&sensor=7&start=1&end=20", 400, "INVALID_QUERY_VALUE"),
    ("INVALID_SENSOR", "/api/history?split=train&unit=1&sensor=22&start=1&end=20", 400, "INVALID_SENSOR"),
    ("MISSING_REQUIRED_PARAMETER", "/api/history?split=train&unit=1&sensor=7&start=1", 400, "INVALID_QUERY_VALUE"),
    ("DUPLICATE_QUERY_PARAMETER", "/api/units?split=train&split=test", 400, "INVALID_QUERY_VALUE"),
    ("UNKNOWN_QUERY_PARAMETER", "/api/units?split=train&foo=1", 400, "INVALID_QUERY_VALUE"),
    ("NON_INTEGER_CYCLE", "/api/history?split=train&unit=1&sensor=7&start=x&end=20", 400, "INVALID_QUERY_VALUE"),
    ("REVERSED_CYCLE_RANGE", "/api/history?split=train&unit=1&sensor=7&start=20&end=1", 400, "INVALID_QUERY_VALUE"),
    ("ABSENT_OBSERVATION", "/api/history?split=train&unit=999&sensor=7&start=1&end=20", 404, "OBSERVATION_NOT_FOUND"),
]


def main() -> None:
    results = []
    for name, path, expected_status, expected_code in CASES:
        try:
            with urlopen(BASE + path, timeout=10) as response:
                status = response.status
                payload = json.load(response)
        except HTTPError as error:
            status = error.code
            payload = json.load(error)
        actual_code = payload.get("error", {}).get("code")
        results.append({
            "case": name,
            "path": path,
            "expected_http": expected_status,
            "actual_http": status,
            "expected_code": expected_code,
            "actual_code": actual_code,
            "error_json": payload,
            "pass": status == expected_status and actual_code == expected_code,
        })
    passed = sum(item["pass"] for item in results)
    print(json.dumps({"passed": passed, "total": len(results), "results": results}, sort_keys=True))
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
