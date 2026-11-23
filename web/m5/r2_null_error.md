# M5 R2 Null and Missing Data Evidence

- Method: isolated `TEST_ONLY` fixtures
- Production FD001 source modified: NO
- Fixture treated as Raw Source evidence: NO
- Result: **PASS**

| Fixture | Actual Browser state | Result |
|---|---|---|
| Null optional field | Success; required Sensor value remained 554.36; one row | PASS |
| Null required Sensor value | Source Not Validated; 0 rows; no Prompt | PASS |
| Missing required Sensor field | Source Not Validated; 0 rows; no Prompt | PASS |
| Non-finite Sensor value | Source Not Validated; 0 rows; no Prompt | PASS |
| Source validation failure | Fixture HTTP 503; Source Not Validated; 0 rows | PASS |

No invalid value became 0, no interpolation occurred, no previous value was reused, and no missing observation was fabricated. Invalid states cleared Chart/Table/Evidence and disabled Generate/Copy.

The fixture source is `web/m5/r2_fixture_server.py`. Evidence screenshot: `web/m5/browser_evidence/r2_null_required_error.png`.
