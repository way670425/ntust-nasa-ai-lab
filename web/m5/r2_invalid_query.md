# M5 R2 Invalid Query Verification

## Real API contract

Command: `PYTHONDONTWRITEBYTECODE=1 python3 web/m5/invalid_query_checks.py`

- Exit code: 0
- Result: 9/9 passed

| Case | HTTP | Error code | Result |
|---|---:|---|---|
| Invalid Split | 400 | `INVALID_SPLIT` | PASS |
| Invalid Unit | 400 | `INVALID_QUERY_VALUE` | PASS |
| Invalid Sensor | 400 | `INVALID_SENSOR` | PASS |
| Missing required parameter | 400 | `INVALID_QUERY_VALUE` | PASS |
| Duplicate parameter | 400 | `INVALID_QUERY_VALUE` | PASS |
| Unknown parameter | 400 | `INVALID_QUERY_VALUE` | PASS |
| Non-integer Cycle | 400 | `INVALID_QUERY_VALUE` | PASS |
| Reversed Cycle range | 400 | `INVALID_QUERY_VALUE` | PASS |
| Absent observation | 404 | `OBSERVATION_NOT_FOUND` | PASS |

All messages were bounded JSON errors and exposed no private path.

## Browser state verification

- A real valid API result was loaded before each isolated UI error injection.
- HTTP 400 displayed `Query Validation Error`.
- HTTP 404 displayed `Observation Not Found`.
- HTTP 503 displayed `Source Not Validated`.
- Each state cleared Chart, Table and Evidence, invalidated Prompt, and disabled Generate/Copy.
- This TEST_ONLY injection verified UI classification only; it was not used as source-integrity evidence.
- UAT_13 used the Production validation path and emitted zero History requests containing `start=20&end=1`.

Evidence: `web/m5/browser_evidence/r2_error_400_404_503.png` and `r2_invalid_query_20_1.png`.
