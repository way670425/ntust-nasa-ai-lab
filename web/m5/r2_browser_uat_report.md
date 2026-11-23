# M5 R2 Full Browser UAT Report

- Work item: `WO-M5-WEB-UAT-001-R2`
- Base commit: `484617a5e6719c2e9cff52e2ee4434b7d6a2dc04`
- Execution: 2026-11-23 11:33:05–11:33:10 CST (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- OS: macOS 27.0.1 arm64
- Production URL: `http://127.0.0.1:8001/`
- Result: **21/21 Browser cases passed in the completed R2 run**
- Authority boundary: Worker test result only; not an M5 Final Gate decision.

## Case results

| Case | Exact Browser action / query | Expected | Actual | Evidence | Result |
|---|---|---|---|---|---|
| UAT_01 | Open real local website | Normal load | Source Validated and Success visible | `r2_initial_website.png` | PASS |
| UAT_02 | Inspect TRAIN Unit 1 | Correct Split/Unit | TRAIN Unit 1 selected | `r2_initial_website.png` | PASS |
| UAT_03 | Inspect `sensor_7` | Correct Sensor | `sensor_7` selected | `r2_initial_website.png` | PASS |
| UAT_04 | Inspect Cycle 1–20 | Correct query | Start 1 / End 20 | `r2_initial_website.png` | PASS |
| UAT_05 | Inspect Trend for TRAIN/1/sensor_7/1-20 | 20 API points | Browser count 20; API count 20 | `r2_train_unit_1_sensor_7_cycles_1_20.png` | PASS |
| UAT_06 | Count Table rows | 20 rows | 20 Browser data rows | same as UAT_05 | PASS |
| UAT_07 | Click final Chart point | Evidence/Prompt update | Cycle 20 selected with physical line 20 | `r2_selected_chart_point.png` | PASS |
| UAT_08 | Click Cycle 5 Table row | Evidence/Prompt update | Cycle 5 selected with physical line 5 | `r2_selected_table_row.png` | PASS |
| UAT_09 | Switch TRAIN to TEST | No TRAIN residue | TEST and `test_FD001.txt`; TRAIN file absent from Prompt | `r2_changed_unit_sensor_cycle.png` | PASS |
| UAT_10 | Switch to TEST Unit 2 | Unit/range reset | Unit 2 with range 1–20 | same as UAT_09 | PASS |
| UAT_11 | Switch to `sensor_8` | Chart/Table/Prompt synchronized | Evidence and Prompt identify `sensor_8` | same as UAT_09 | PASS |
| UAT_12 | Set TEST/Unit2/sensor_8/2-6 | Count/range correct | 5 rows; Prompt range 2–6 | same as UAT_09 | PASS |
| UAT_13 | Enter Start 20 / End 1 | Clear stale state; no invalid fetch | Exact error; 0 Chart/Table; N/A Evidence; disabled Copy; 0 invalid requests | `r2_invalid_query_20_1.png` | PASS |
| UAT_14 | Inject isolated History HTTP 400/404/503 after valid data | Correct UI classification and clearing | Query Validation Error / Observation Not Found / Source Not Validated; all cleared | `r2_error_400_404_503.png` | PASS |
| UAT_15 | Stop verified API PID 59558, keep Frontend, query | Connection Error and clearing | Frontend HTTP 200; Connection Error; old state cleared | `r2_api_disconnected.png` | PASS |
| UAT_16 | Start API PID 60051 and query again | Recovery with valid source | Health validated/read-only; 20 rows; Prompt/Copy restored | `r2_api_recovered.png` | PASS |
| UAT_17 | Open five isolated Null/Missing fixtures | No zero-fill/interpolation/fabrication | Optional null preserved value; four invalid required/source cases rejected | `r2_null_required_error.png` | PASS |
| UAT_18 | Inspect current Prompt fields/classes/formulas | Current identity, provenance and M2 scope | All required fragments; Mean and Delta reproduced | `r2_evidence_prompt_copy.png` | PASS |
| UAT_19 | Click Copy and read Browser Clipboard | Exact equality | 5580 visible chars = 5580 clipboard chars | same as UAT_18 | PASS |
| UAT_20 | Delay sensor_7, switch to sensor_8, release old request | Old response cannot overwrite new | Evidence and Prompt remained `sensor_8` | `r2_stale_response_prevented.png` | PASS |
| UAT_21 | Inspect inference restrictions | No fabricated claims | Baseline/diagnosis/health/RUL checks false; health and RUL explicitly UNKNOWN | same as UAT_20 | PASS |

Each case's exact timestamp, query, expected, actual and evidence path is also preserved in `web/m5/r2_browser_results.json`.

## Screenshot set

The completed run created 12 full-page Google Chrome screenshots under `web/m5/browser_evidence/`:

- `r2_initial_website.png`
- `r2_train_unit_1_sensor_7_cycles_1_20.png`
- `r2_selected_chart_point.png`
- `r2_selected_table_row.png`
- `r2_changed_unit_sensor_cycle.png`
- `r2_invalid_query_20_1.png`
- `r2_error_400_404_503.png`
- `r2_api_disconnected.png`
- `r2_api_recovered.png`
- `r2_null_required_error.png`
- `r2_evidence_prompt_copy.png`
- `r2_stale_response_prevented.png`

No screenshot contains credentials, tokens, private filesystem paths or a complete raw FD001 source.

## Execution notes

Two earlier attempts stopped because of R2 test-tool defects before completing all cases: an incorrect Playwright `arg` call and a route-handler closure error. The evidence tool alone was corrected inside the authorized boundary. The table above is exclusively the fresh, completed third run; no partial result was counted.
