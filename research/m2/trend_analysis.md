# FD001 Cycle-Based Sensor Trend Analysis

Work item: `WO-M2-RESEARCH-001-B`

This report uses NASA C-MAPSS simulated turbofan degradation observations, not physical engine field measurements. A trend is descriptive and is not a diagnosis or an RUL prediction.

## Method

For each selected `(split, unit_id, sensor_id)` trajectory, rows are sorted by cycle. The reported slope is the ordinary least-squares coefficient:

`slope = sum((cycle_i-cycle_mean)*(value_i-value_mean)) / sum((cycle_i-cycle_mean)^2)`

Slope unit is recorded Sensor-value units per cycle. The physical units of the 21 Sensor fields are not defined by this contract. Direction is `INCREASING` for slope greater than `1e-12`, `DECREASING` for slope less than `-1e-12`, and `FLAT` otherwise. `delta` is last value minus first value and may differ in sign from the fitted slope because the slope uses every observation.

TRAIN and TEST are separate splits. A shared numeric Unit ID does not identify the same engine across splits. The last observed TEST cycle is truncated-before-failure data and must not be treated as a failure time.

## Source identity

- TRAIN: `train_FD001.txt`, SHA-256 `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- TEST: `test_FD001.txt`, SHA-256 `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851`

## Reproducible cases

| Split | Unit | Sensor | Cycle range | Source physical lines (1-based) | Parsed rows (0-based) | First | Last | Min | Max | Mean | Delta | OLS slope | Direction |
|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| TRAIN | 1 | 2 | 1–192 | 1–192 | 0–191 | 641.82 | 643.54 | 641.71 | 644.21 | 642.621042 | 1.72 | 0.006073604 | INCREASING |
| TRAIN | 1 | 3 | 1–192 | 1–192 | 0–191 | 1589.70 | 1601.41 | 1577.60 | 1605.44 | 1589.485521 | 11.71 | 0.060471086 | INCREASING |
| TRAIN | 1 | 4 | 1–192 | 1–192 | 0–191 | 1400.60 | 1427.20 | 1393.58 | 1432.52 | 1407.262135 | 26.60 | 0.127024803 | INCREASING |
| TEST | 1 | 2 | 1–31 | 1–31 | 0–30 | 643.02 | 642.58 | 641.71 | 643.02 | 642.319032 | -0.44 | 0.001475806 | INCREASING |
| TEST | 1 | 3 | 1–31 | 1–31 | 0–30 | 1585.29 | 1581.22 | 1579.12 | 1594.29 | 1585.647742 | -4.07 | 0.044862903 | INCREASING |
| TEST | 1 | 4 | 1–31 | 1–31 | 0–30 | 1398.21 | 1398.91 | 1395.09 | 1412.28 | 1401.526129 | 0.70 | -0.019548387 | DECREASING |

The endpoint source-line ranges above are sufficient to locate the selected trajectories without publishing the full Raw Index or source rows. Full raw indexes remain local. Values and slopes are generated from the verified source by `research/m2/m2b/scripts/analyze_fd001_m2b.py`.

## Interpretation boundary

- No selected trend is labeled as a failure, fault, diagnosis, or RUL prediction.
- The TEST Unit 1 final observation at cycle 31 is not declared to be a failure point.
- `RUL_FD001.txt` is not used as a Sensor observation.
- M1 synthetic data is not used.
