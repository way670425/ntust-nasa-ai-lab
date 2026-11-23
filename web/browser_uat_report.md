# FD001 M4 Browser UAT Report

- Work item: `WO-M4-WEB-EVIDENCE-001`
- Date: 2026-11-23 (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- OS: macOS 27.0.1 arm64
- Mode: visible Chrome controlled through real UI interactions
- Browser URL: `http://127.0.0.1:8001/`
- API: accepted M3-A service at `127.0.0.1:8000`
- Startup: `PYTHONDONTWRITEBYTECODE=1 python3 web/run_server.py` and `PYTHONDONTWRITEBYTECODE=1 python3 web/frontend_server.py`
- Result: **16 PASS / 0 FAIL**

## Cases

| ID | Operation | Active selection | Expected | Actual | Result |
|---|---|---|---|---|---|
| UAT_01 | Open local website | Default load | Page is interactive | Title, disclosure, controls, validated badge, Chart, Table, Evidence and Prompt loaded | PASS |
| UAT_02 | Select TRAIN Unit 1 Sensor 7 | TRAIN / 1 / sensor_7 | Selectors match query | Status and Chart title showed the requested selection | PASS |
| UAT_03 | Set Cycle Range 1–20 | Cycles 1–20 | Range matches query | Start 1, End 20 and 20 observations shown | PASS |
| UAT_04 | Inspect Trend Chart | TRAIN / 1 / sensor_7 / 1–20 | 20 real API points | Chart badge showed 20; plotted values came from the same 20 parsed API observations | PASS |
| UAT_05 | Inspect Observation Table | Same selection | 20 rows match API | Browser counted 20 rows; values and provenance matched API/source comparison | PASS |
| UAT_06 | Click Chart Observation | Cycle 20 | Evidence updates | Highlight moved to Cycle 20; physical line 20, parsed row 19; Prompt selected Cycle 20 | PASS |
| UAT_07 | Click Table Observation | Cycle 10 | Evidence and Prompt update | Selected Cycle 10; Prompt source line 10 and parsed row 9 | PASS |
| UAT_08 | Switch TRAIN to TEST | TEST / 1 / sensor_7 | No cross-Split residue | TEST status, title, Prompt and `test_FD001.txt` replaced TRAIN state | PASS |
| UAT_09 | Switch Engine Unit | TEST / 2 / sensor_7 | Unit and cycles update | Chart title and Evidence used Unit 2; current range reset to 1–20 | PASS |
| UAT_10 | Switch Sensor | TEST / 2 / sensor_8 | Chart/Table/Evidence update | All active UI and Prompt fields used sensor_8 | PASS |
| UAT_11 | Change Cycle Range | TEST / 2 / sensor_8 / 2–10 | Query/display match | Title and Prompt showed 2–10; Table contained 9 rows | PASS |
| UAT_12 | Generate Evidence Prompt | Current validated History | Prompt maps current evidence | OBSERVED, DERIVED, INFERRED and UNKNOWN plus required disclosures were present | PASS |
| UAT_13 | Copy Evidence Prompt | TRAIN / 1 / sensor_7 / selected Cycle 10 | Clipboard equals visible Prompt | Success feedback shown; browser Clipboard and UI were exactly equal at 2,760 characters | PASS |
| UAT_14 | Exercise 400/404/503/connection errors | TEST_ONLY harness | Safe classification; no stale data | Correct four labels shown; Prompt invalid and Copy disabled in every error state | PASS |
| UAT_15 | Rapidly switch selections | TRAIN immediately replaced by TEST | Old response cannot overwrite new | Final title/status/Prompt were exclusively TEST Unit 1 sensor_8 | PASS |
| UAT_16 | Review page and Prompt claims | Production UI | No fabricated diagnosis, threshold or RUL | Numeric threshold, health score, RUL, confirmed diagnosis and external-send scans all returned false | PASS |

## Visual evidence

- `web/browser_evidence/m4_initial.png`: initial validated website and TRAIN selection.
- `web/browser_evidence/m4_chart_selected_evidence.png`: 20-point Chart and Cycle 20 provenance.
- `web/browser_evidence/m4_evidence_prompt.png`: Cycle 10 Prompt and visible copy-success feedback.
- `web/browser_evidence/m4_switched_selection.png`: TEST Unit 2 sensor_8 Evidence and Prompt.
- Detailed observations: `web/browser_evidence/browser_observations.md`.

The screenshots came from the real browser and contain no credential, secret, local absolute path, or raw-source row collection. Initial and TRAIN-selection states share the same safe screenshot; Chart/Table and selected Evidence share the Chart/Evidence screenshot.

## Failure and correction history

1. The first automated run found one incorrect test expectation: rejected stale/altered/unavailable copy attempts correctly made zero Clipboard writes, while the test expected one. The assertion was corrected; the full test suite then passed.
2. The first M4 browser load reused the old unversioned ES module cache, so the new HTML appeared while Prompt stayed unavailable. Version parameters were added to both `app.js` and `state.mjs`; a fresh load generated the Prompt correctly.
3. The CUA clipboard bridge did not expose the page Clipboard buffer even though the browser reported a successful write. This was not treated as proof. Exact equality was subsequently reproduced twice: macOS `pbpaste` versus an API-generated expected Prompt, and Playwright-granted browser Clipboard versus the visible Prompt.
4. An initial approximate Canvas coordinate did not hit a point and was not counted. The final Chrome run calculated the same Canvas scale used by the application, clicked the exact Cycle 20 point, and verified the resulting Evidence and Prompt.

## Boundary

The 400/404/503 scenarios use the committed, clearly marked TEST_ONLY harness; production data, Chart/Table values, provenance, Prompt and copy checks use the accepted real API. This Worker report is evidence for STUDENT-WEB Brain review, not an M4 Gate decision and not authorization for M5.
