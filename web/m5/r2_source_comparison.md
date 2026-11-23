# M5 R2 Source Comparison

- Fixed query: `/api/history?split=train&unit=1&sensor=7&start=1&end=20`
- Live API: HTTP 200
- API observations: 20
- Independent raw observations: 20
- Result: **PASS, differences NONE**

## Recomputed source hashes

| Source | SHA-256 | Result |
|---|---|---|
| TRAIN | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` | MATCH |
| TEST | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` | MATCH |
| TEST_RUL | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` | MATCH |

## Independent checks

- Each source row was required to contain 26 fields.
- `sensor_7` was read from one-based source column 12 (`fields[11]`).
- Cycle: 20/20 match.
- Sensor value: 20/20 match.
- Safe source basename: 20/20 `train_FD001.txt` match.
- Source SHA-256: 20/20 match.
- Physical Line (1-based): 20/20 match.
- Parsed Row Index (0-based): 20/20 match.
- Browser Table: 20 data rows.
- Browser Chart indicator: 20 observations.
- Selected Cycle 1 Evidence: physical line 1, parsed row 0.
- Prompt: TRAIN Unit 1, `sensor_7`, Cycles 1–20, 20 observations.

Exact command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 web/frontend/tests/verify_api_source.py
```

It exited 0 before interruption and again after real API recovery. No raw row collection or derived CSV was created or committed.
