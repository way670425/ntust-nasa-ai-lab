# M5 UAT_13 R1 Test Execution

- Work item: `WO-M5-WEB-UAT-001-R1`
- Date: 2026-11-23 (Asia/Taipei)
- Base commit: `811881463bea6140aeb5adcf591693c5e1834f1b`

## Required regression results

| Test | Exact command | Actual result | Exit |
|---|---|---|---:|
| API regression | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/tests -v` | 14 passed, 0 failed, 0 errors | 0 |
| Frontend state and Prompt | `node --test web/frontend/tests/state.test.mjs web/frontend/tests/evidence_prompt.test.mjs` | 22 passed, 0 failed | 0 |
| Frontend server | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/frontend/tests -p 'test_*.py' -v` | 4 passed, 0 failed, 0 errors | 0 |
| R1 Browser interaction | `/opt/anaconda3/bin/python3 web/frontend/tests/r1_invalid_state_browser.py --url 'http://127.0.0.1:8001/?v=m5-r1' --evidence-dir web/m5/browser_evidence` | R1_01–R1_07: 7 passed, 0 failed | 0 |
| Real API row comparison | `PYTHONDONTWRITEBYTECODE=1 python3 web/frontend/tests/verify_api_source.py` | 20 API rows matched 20 raw TRAIN rows; differences NONE | 0 |
| Invalid Query API checks | `PYTHONDONTWRITEBYTECODE=1 python3 web/m5/invalid_query_checks.py` | 9 passed, 0 failed | 0 |

Total counted assertions/cases across the required suites and supplemental API checks: **76 passed, 0 failed, 0 errors** (14 + 22 + 4 + 7 + 20 row matches + 9 invalid-query cases). The row comparison is reported as 20 matched rows, not as a Python unittest count.

## R1 interaction cases

| ID | Result | Evidence |
|---|---|---|
| R1_01 Invalid Range Clears Old Results | PASS | Success, Chart, Table and Evidence cleared |
| R1_02 Prompt Invalidated And Copy Disabled | PASS | Prompt null-equivalent UI; Generate and Copy disabled |
| R1_03 No History Request For Invalid Range | PASS | 0 requests containing `start=20&end=1` |
| R1_04 Pending History Request Cannot Restore Success | PASS | delayed request released; error state remained |
| R1_05 Correcting Range Restores Normal Query | PASS | 1–20 restored 20 observations and current evidence/prompt |
| R1_06 Other Invalid Cycle Ranges | PASS | non-integer, zero, negative, outside and empty cases fail closed |
| R1_07 Existing Selectors Continue To Work | PASS | TRAIN/TEST, Unit, Sensor, valid query and Clipboard copy |

## Startup and source integrity

- Stable API PID: 56938; Frontend PID: 56942.
- API and Frontend returned HTTP 200.
- TRAIN SHA-256: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- TEST SHA-256: `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851`
- TEST_RUL SHA-256: `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca`

## Transparent rerun notes

- The first in-sandbox API and Frontend-server unittest attempts could not bind loopback ports and exited 1 with `PermissionError: Operation not permitted`. The exact commands were rerun with local-loopback permission and passed 14/14 and 4/4; only those completed reruns are acceptance evidence.
- The first R1 Browser script execution exited 1 because its network assertion counted a legal intermediate 20/20 request while the user moved from 1/20 to 20/1. The test was corrected to assert the actual contract: no 20/1 request and no new request after the range became invalid. The product code was not changed for this test correction. The complete rerun passed 7/7.
- The long-running services are reported as running and healthy, not as exit-code-zero commands.

## Limitation

Only the authorized UAT_13 correction and regression scope was executed. The full parent M5 UAT was not resumed.
