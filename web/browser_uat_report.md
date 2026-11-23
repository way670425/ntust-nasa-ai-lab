# FD001 Prompt Enhancement Browser UAT Report

- Work item: `WO-M4-WEB-PROMPT-ENHANCE-001`
- Date: 2026-11-23 (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- OS: macOS 27.0.1 arm64
- Mode: visible real Chrome through CUA and Playwright interaction
- URL: `http://127.0.0.1:8001/`
- Startup: `PYTHONDONTWRITEBYTECODE=1 python3 web/run_server.py` and `PYTHONDONTWRITEBYTECODE=1 python3 web/frontend_server.py`
- Result: **15 PASS / 0 FAIL**

| ID | Operation | Expected | Actual | Result |
|---|---|---|---|---|
| UAT_01 | Open real website | Source is validated | Badge showed `Source Validated`; API-backed page was interactive | PASS |
| UAT_02 | TRAIN Unit 1 sensor_7, cycles 1–20 | Current selection is exact | Status, Chart, 20 Table rows and Prompt matched the selection | PASS |
| UAT_03 | Inspect Prompt Current Selection | Prompt maps live API | Dataset/Split/Unit/Sensor/range/count/selected value and provenance matched API | PASS |
| UAT_04 | Inspect Field Semantics | sensor_7 is source column 12 | Prompt showed 26 fields, 1+1+3+21 mapping, one-based column 12 and unspecified unit | PASS |
| UAT_05 | Inspect Data Quality Context | M2 report source is explicit | Prompt cited report, contract, work item, Metadata version and TRAIN 20,631/100 counts | PASS |
| UAT_06 | Switch TRAIN to TEST | Quality Scope changes without residue | TEST 13,096/100, TEST source/hash and `Applicable Split: TEST`; no TRAIN quality Scope remained | PASS |
| UAT_07 | Switch to Unit 2 | Old Unit is removed | Prompt used Unit 2 only | PASS |
| UAT_08 | Switch to sensor_21 | Column position updates | Prompt changed selected Sensor to sensor_21 and one-based source column 26 | PASS |
| UAT_09 | Change range to 2–10 | DERIVED range/count update | Table contained 9 rows; Prompt/Mean/Delta calculation source used cycles 2–10 | PASS |
| UAT_10 | Click Chart Cycle 20 | Provenance and Prompt synchronize | Selected Cycle 20; physical line 20, parsed row 19; Prompt selected Cycle 20 | PASS |
| UAT_11 | Click Table Cycle 5 | Prompt synchronizes | TEST Unit 2 sensor_21 selected Cycle 5; line 36 / parsed row 35 | PASS |
| UAT_12 | Copy Prompt | Clipboard equals UI | Browser Clipboard and visible Prompt were exactly equal at 5,582 characters | PASS |
| UAT_13 | Exercise 400/404/503/connection errors | Old Prompt is unusable | Correct safe labels; Prompt invalidated and Copy disabled in all four TEST_ONLY states | PASS |
| UAT_14 | Rapid TRAIN then TEST switch | No stale Prompt | Final Chart and Prompt were exclusively TEST with TEST quality Scope | PASS |
| UAT_15 | Review External AI instructions | Complete, bounded, no fabricated claims | Required instructions present; numeric threshold/score/RUL scans false; local-copy/no-send disclosure present | PASS |

## Visual evidence

- `web/browser_evidence/m4_prompt_enhance_train.png`: TRAIN Prompt, current selection and Field Semantics.
- `web/browser_evidence/m4_prompt_enhance_chart_evidence.png`: real Chart Cycle 20 selection and provenance.
- `web/browser_evidence/m4_prompt_enhance_test.png`: TEST Unit 2 sensor_21 Prompt and one-based column 26.
- `web/browser_evidence/browser_observations.md`: detailed observations.

Screenshots show only safe website content: no private absolute path, credential, secret, full Raw Index or bulk reconstructable source rows.

## Defect and correction record

No application defect was found during the final 15-case run. The exact Canvas point and Clipboard read-back were exercised in a second visible Chrome context with explicit local Clipboard permission; this supplements rather than replaces the CUA interactions. TEST_ONLY error injection was not used as source-integrity evidence.

This is Worker evidence for STUDENT-WEB Brain review. It is not an M4 Gate decision and does not authorize M5.
