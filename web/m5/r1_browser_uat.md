# M5 UAT_13 Targeted Rework Browser Evidence

- Work item: `WO-M5-WEB-UAT-001-R1`
- Parent work item: `WO-M5-WEB-UAT-001`
- Execution time: 2026-11-23 11:14–11:16 CST (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- OS: macOS 27.0.1 arm64
- Production URL: `http://127.0.0.1:8001/?v=m5-r1`
- API health: HTTP 200, `data_validated=true`, `read_only=true`
- Result: **PASS for targeted UAT_13 rerun**
- Scope boundary: this is not a complete M5 UAT rerun and is not a Gate declaration.

## Real API and visible Browser sequence

1. Opened the real local Frontend backed by the real local read-only API.
2. Confirmed TRAIN, Unit 1, `sensor_7`, Cycles 1–20 displayed Success, 20 Chart/Table observations, source evidence, a current Evidence Prompt and enabled Copy.
3. Entered Start Cycle `20`, then End Cycle `1`.
4. Confirmed the invalid values remained in their fields.
5. Confirmed `Query Validation Error` and exact detail `Start Cycle cannot exceed End Cycle.`
6. Confirmed Success disappeared; Chart count was 0; Table data rows were 0; all 11 Evidence values were `N/A`; selected Cycle was `No point`; Prompt was invalid; Generate and Copy were disabled.
7. Corrected the range to 1–20 and selected Load observations.
8. Confirmed Success returned with 20 current observations, `train_FD001.txt` evidence, a rebuilt Prompt and enabled Copy.

The visible Chrome rerun independently observed the same invalid and recovery states as the automated interaction regression.

## Network and race evidence

- Automated Chrome network capture contained no `/api/history` request with `start=20&end=1`.
- Invalid 20/1 History requests: `0`.
- A TEST_ONLY Browser interception held one otherwise-valid History request pending. Entering 20/1 aborted or invalidated that request identity; releasing the interception did not restore Success, Chart, Table, Evidence or Prompt.
- The run recorded two failed History requests, consistent with requests cancelled during invalidation/race coverage; no failed request restored state.
- The race fixture did not provide Raw Source Evidence and was used only for request timing.

## Expected versus actual

| Requirement | Actual | Result |
|---|---|---|
| Exact validation title/message | `Query Validation Error` / `Start Cycle cannot exceed End Cycle.` | PASS |
| Preserve invalid inputs | Start 20 / End 1 remained visible | PASS |
| Clear old Success | Error state replaced Success | PASS |
| Clear Chart/Table | 0 observations / 0 data rows | PASS |
| Clear Evidence | 11/11 fields showed `N/A` | PASS |
| Invalidate Prompt | Safe unavailable text shown | PASS |
| Disable Generate/Copy | Both disabled | PASS |
| No invalid History request | 0 requests for 20/1 | PASS |
| Pending response cannot restore stale data | Error state remained after release | PASS |
| Valid-range recovery | 20 observations and current evidence/prompt restored | PASS |

## Browser screenshots

- `web/m5/browser_evidence/r1_initial_valid_query.png`
- `web/m5/browser_evidence/r1_invalid_20_1_cleared.png`
- `web/m5/browser_evidence/r1_invalid_prompt_disabled.png`
- `web/m5/browser_evidence/r1_corrected_valid_query.png`
- `web/m5/browser_evidence/r1_pending_request_cancelled.png`

All screenshots came from Google Chrome against the local application. They contain no credentials, private absolute paths or complete raw FD001 files.

## Preserved prior failure

The original pre-fix failure remains unchanged in `web/m5/browser_uat_report.md`. This R1 report records only the authorized correction rerun.
