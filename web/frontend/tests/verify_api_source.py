#!/usr/bin/env python3
"""Independently compare the required live API query with local raw TRAIN rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE = PROJECT_ROOT / "data" / "FD001" / "train_FD001.txt"
URL = "http://127.0.0.1:8000/api/history?split=train&unit=1&sensor=7&start=1&end=20"
EXPECTED_SHA = "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8"


def main() -> None:
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_hash != EXPECTED_SHA:
        raise SystemExit("FAIL: TRAIN source SHA-256 mismatch")

    with urlopen(URL, timeout=15) as response:
        if response.status != 200:
            raise SystemExit(f"FAIL: API HTTP {response.status}")
        payload = json.load(response)

    api_rows = payload.get("observations", [])
    if payload.get("observation_count") != 20 or len(api_rows) != 20:
        raise SystemExit("FAIL: API observation count is not 20")

    raw_rows: list[dict[str, int | float]] = []
    parsed_index = 0
    with SOURCE.open("r", encoding="utf-8", newline="") as source:
        for physical_line, raw_line in enumerate(source, start=1):
            fields = raw_line.split()
            if len(fields) != 26:
                raise SystemExit(f"FAIL: invalid field count at physical line {physical_line}")
            unit_id = int(fields[0])
            cycle = int(fields[1])
            if unit_id == 1 and 1 <= cycle <= 20:
                raw_rows.append(
                    {
                        "cycle": cycle,
                        "value": float(fields[11]),
                        "physical_line": physical_line,
                        "parsed_index": parsed_index,
                    }
                )
            parsed_index += 1

    if len(raw_rows) != 20:
        raise SystemExit("FAIL: independent raw row count is not 20")

    differences: list[str] = []
    for api_row, raw_row in zip(api_rows, raw_rows):
        evidence = api_row.get("source_evidence", {})
        checks = {
            "cycle": api_row.get("cycle") == raw_row["cycle"],
            "sensor": api_row.get("sensor") == "sensor_7",
            "value": api_row.get("value") == raw_row["value"],
            "source_file": evidence.get("source_file") == "train_FD001.txt",
            "source_sha256": evidence.get("source_sha256") == EXPECTED_SHA,
            "physical_line": evidence.get("source_physical_line_1_based") == raw_row["physical_line"],
            "parsed_index": evidence.get("parsed_row_index_0_based") == raw_row["parsed_index"],
        }
        for name, passed in checks.items():
            if not passed:
                differences.append(f"cycle {raw_row['cycle']}: {name}")

    if differences:
        raise SystemExit("FAIL: " + ", ".join(differences))

    print(
        json.dumps(
            {
                "result": "PASS",
                "query": URL.removeprefix("http://127.0.0.1:8000"),
                "source_sha256": source_hash,
                "api_count": len(api_rows),
                "raw_count": len(raw_rows),
                "matched": 20,
                "differences": "NONE",
                "first_cycle": raw_rows[0]["cycle"],
                "last_cycle": raw_rows[-1]["cycle"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
