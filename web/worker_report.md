# Web Own Worker R1 Execution Report

- Type: `WORKER_TO_BRAIN_REWORK_RETURN`
- Work item: `WO-M3-WEB-API-001-R1`
- Parent work item: `WO-M3-WEB-API-001`
- From: Web Own Worker
- To: STUDENT-WEB Brain
- Execution date: 2026-11-22 (Asia/Taipei)
- Worker execution: `SUCCESS` (candidate delivery; Brain verification required)
- GitHub AGENTS read: `TRUE`
- Base commit: `a62f0fa6897d2aae2d84d7f6930d1b268f003c26`
- Result commit: the Git commit containing this report; full SHA is reported in the external Worker return after push
- Worker Gate declaration: `PROHIBITED`

## R1 scope and results

| Check | Worker result |
|---|---|
| Strict query validation | PASS |
| Complete Catalog schema | PASS |
| Invalid Sensor tests | PASS |
| API regression | PASS |
| Source-row verification | PASS |
| Source-hash verification | PASS |
| Null policy | PASS |
| Error contract | PASS |
| Read-only verification | PASS |

The changes are limited to the three authorized corrections:

1. `/api/health` and `/api/catalog` reject all query parameters; `/api/units` permits only `split`; `/api/history` permits only `split`, `unit`, `sensor`, `start`, and `end`. Unknown, repeated, or missing required parameters return HTTP 400 with `INVALID_QUERY_VALUE`.
2. Catalog `observation_schema` now returns all 26 source fields in one-based source-column order. Every entry contains `name`, `data_type`, `nullable`, `source_column_position`, and `query_semantics`. All fields are non-nullable; physical units remain source-defined or unspecified; TEST_RUL remains an independent positional label rather than a Sensor History Split.
3. Invalid Sensor selectors distinguish malformed/non-integer values (`INVALID_QUERY_VALUE`) from integer IDs outside 1–21 (`INVALID_SENSOR`). Normal `sensor=7` behavior is unchanged.

## Regression and source evidence

The required TRAIN Unit 1, Sensor 7, Cycle 1–20 query returned 20 observations. A test-side parser independently compared all 20 source values, cycles, source basenames, SHA-256 values, physical line numbers, and parsed row indexes. Comparison result: 20/20 matched. Cycle 1 mapped to physical line 1 / parsed row 0; Cycle 20 mapped to physical line 20 / parsed row 19. No cross-Split, cross-Unit, or out-of-range observations were returned.

Source SHA-256 values after the R1 test run:

- TRAIN: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- TEST: `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851`
- TEST_RUL: `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca`

## Test evidence

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/tests -v
```

Result: exit code `0`; 14 tests run; 14 passed; 0 failed; 0 errors.

The suite covers the five original endpoint calls, eight strict-parameter cases, all 26 Catalog fields, seven invalid-Sensor cases, the normal Sensor 7 case, source hash and row verification, null handling, safe error responses, TRAIN/TEST isolation, missing/tampered/malformed sources, and POST/PUT/PATCH/DELETE rejection.

## Changed files

- `web/fd001_api/app.py`
- `web/tests/test_api.py`
- `web/README.md`
- `web/worker_report.md`

No Loader, Research, FD001 source, Raw Index, unrelated code, or private configuration was modified or staged.

## STOP status

- `STOP_IF_TRIGGERED: NONE`
- `GITHUB_PUSH`: recorded in the external Worker return after delivery
- `RETURN_TO: STUDENT-WEB Brain`

This report is Worker-generated execution evidence. It is not an M3-A Gate decision and does not authorize M3-B.
