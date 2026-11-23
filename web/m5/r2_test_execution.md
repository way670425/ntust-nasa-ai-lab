# M5 R2 Test Execution

- Date: 2026-11-23 (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- OS: macOS 27.0.1 arm64
- Initial API PID: 59558
- Recovered API PID: 60051
- Frontend PID: 59562

## Completed commands

| Test | Exact command | Result | Exit |
|---|---|---|---:|
| API regression | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/tests -v` | 14 passed, 0 failed/errors | 0 |
| Frontend state/Prompt | `node --test web/frontend/tests/state.test.mjs web/frontend/tests/evidence_prompt.test.mjs` | 22 passed, 0 failed | 0 |
| Frontend server | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/frontend/tests -p 'test_*.py' -v` | 4 passed, 0 failed/errors | 0 |
| R1 Browser regression | `/opt/anaconda3/bin/python3 web/frontend/tests/r1_invalid_state_browser.py --url http://127.0.0.1:8001/ --evidence-dir web/m5/r2_r1_regression_evidence` | 7 passed, 0 failed | 0 |
| Raw source comparison | `PYTHONDONTWRITEBYTECODE=1 python3 web/frontend/tests/verify_api_source.py` | 20/20 matched; differences NONE | 0 |
| Invalid Query | `PYTHONDONTWRITEBYTECODE=1 python3 web/m5/invalid_query_checks.py` | 9 passed, 0 failed | 0 |
| Full R2 Browser UAT | `PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python3 web/m5/r2_browser_uat.py --url http://127.0.0.1:8001/?v=m5-r2-final-run --api-url http://127.0.0.1:8000 --api-pid-file /tmp/ntust-nasa-ai-lab-501/api.pid --project-root <project-root> --evidence-dir web/m5/browser_evidence --result-json web/m5/r2_browser_results.json` | 21/21 passed | 0 |

The source comparison was executed before and after API recovery, both Exit 0. Long-running servers were recorded as RUNNING with verified PIDs and HTTP Health, not as Exit 0.

## Transparent harness corrections

- Full Browser attempt 1: Exit 1 before UAT_07 completion because the new R2 test tool used a positional Playwright `wait_for_function` argument.
- Full Browser attempt 2: Exit 1 during UAT_14 because the new R2 route callback allowed Playwright's request argument to replace a Python default parameter.
- Only `web/m5/r2_browser_uat.py` was corrected. No Production source changed.
- Full Browser attempt 3 restarted from UAT_01 and completed 21/21 with Exit 0. No partial case was reused.

## Count summary

- API unittest: 14/14
- Frontend Node tests: 22/22
- Frontend-server unittest: 4/4
- R1 Browser regression: 7/7
- Raw source rows: 20/20
- Invalid Query cases: 9/9
- R2 Browser UAT: 21/21
- Required completed commands with a non-zero final result: NONE
