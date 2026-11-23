# FD001 Browser Evidence Observations

- Work item: `WO-M3-WEB-FRONTEND-001`
- Date: 2026-11-23 (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- Production UAT URL: `http://127.0.0.1:8001/`
- API URL: `http://127.0.0.1:8000/`
- Dataset identity shown: `NASA_CMAPSS_FD001` / `NASA_FD001_LOCAL_TRUSTED`
- Source badge shown: `Source Validated`

## Observed browser states

### Initial validated load

- Split: TRAIN
- Unit: 1
- Sensor: `sensor_7`
- Cycle range: 1–20
- Observation count: 20
- First row: Cycle 1, value 554.36, `train_FD001.txt`, physical line 1, parsed row 0
- Evidence panel matched the first table row.
- Chart displayed 20 unsmoothed observation points without a loading overlay after the UAT fix. The query evidence showed Start Cycle 1 and End Cycle 20.

### Split and Unit changes

- TEST Unit 1 loaded 20 rows for cycles 1–20 and reported available range 1–31.
- First TEST row: Cycle 1, `sensor_7`, value 553.9, `test_FD001.txt`, physical line 1, parsed row 0.
- TEST Unit 2 reported available range 1–49; the first selected observation mapped to physical line 32.

### Sensor, Cycle, and selection consistency

- Changing to `sensor_1` loaded values from the API. All 20 values in the selected TEST window were 518.67 and the chart visibly rendered a horizontal line without fault interpretation.
- Changing the range to cycles 5–10 returned exactly 6 rows.
- First row: Cycle 5, value 518.67, physical line 36, parsed row 35.
- Last row: Cycle 10, value 518.67, physical line 41, parsed row 40.
- Selecting table Cycle 7 updated the highlighted row, chart point, and Evidence to physical line 38 / parsed row 37.
- Selecting the chart point for Cycle 9 updated the highlighted row and Evidence to physical line 40 / parsed row 39.

### Error-state observations

The TEST_ONLY UAT harness served controlled error responses to the real frontend. It was not used for source validation.

| HTTP scenario | UI title | Evidence state |
|---|---|---|
| 400 | Query Validation Error | N/A; 0 rows |
| 404 | Observation Not Found | N/A; 0 rows |
| 503 | Source Not Validated | N/A; 0 rows |
| Backend unavailable / proxy 502 | Connection Error | N/A; 0 rows |

### Stale-response prevention

TEST was selected and immediately replaced by TRAIN. Final browser state contained only:

- Split / Evidence Split: TRAIN
- Chart: `TRAIN · Unit 1 · sensor_7 · Cycles 1–20`
- Status: 20 validated observations loaded from TRAIN Unit 1
- Source file in every rendered row and Evidence: `train_FD001.txt`

No TEST values or TEST evidence remained.

## Interpretation review

The rendered page contained none of these forbidden claims or features: Confirmed Failure, Confirmed Fault, Confirmed Anomaly, Known Failure Cause, Verified Health Score, Unvalidated RUL Prediction, AI Failure Diagnosis, Evidence Prompt Generator, Warning Threshold, or Failure Threshold.

The page explicitly stated that FD001 contains simulated degradation observations and is not physical engine field measurement data, a failure diagnosis, a health score, or an RUL prediction.
