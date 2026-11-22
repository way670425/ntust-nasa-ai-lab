# FD001 Data Quality Summary

Work item: `WO-M2-RESEARCH-001-B`

Dataset ID: `NASA_CMAPSS_FD001`
Source type: `NASA_FD001_LOCAL_TRUSTED`

This report describes NASA C-MAPSS simulated turbofan degradation data. It is not a claim about physical engine field measurements. Statistical variation or an outlying value is not, by itself, an engine-failure diagnosis.

## Source identity

| Split | Local source file | SHA-256 |
|---|---|---|
| TRAIN | `train_FD001.txt` | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` |
| TEST | `test_FD001.txt` | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` |
| TEST_RUL | `RUL_FD001.txt` | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` |

The source files remain local and read-only. They are not included in this publication.

## Method

- Observation denominator: all successfully parsed rows in the named split (`N=20,631` for TRAIN; `N=13,096` for TEST).
- Mean: arithmetic mean, `sum(x_i) / N`.
- Standard deviation: population standard deviation, `sqrt(sum((x_i-mean)^2) / N)`.
- Unique count: count of distinct parsed floating-point values.
- Missing value: an absent required token among the 26 effective fields.
- Non-finite value: a parsed numeric value for which `isfinite(value)` is false.
- Duplicate Unit-Cycle key: every occurrence beyond the first for the same `(split, unit_id, cycle)` pair.
- Invalid cycle: a cycle that is not a positive integer.
- Missing cycle: a value absent from the expected per-unit sequence `1..max(cycle)`.
- Parsing anomaly: a physical source line that does not produce exactly one valid 26-field observation.
- Constant Sensor: exactly one distinct value over the split.
- Near-constant Sensor: non-constant and `(max-min)/max(abs(min),abs(max),1) <= 1e-4`.
- No outlier classification is calculated in this work item.

Displayed decimal values may be rounded; the reproducible script performs calculations using parsed Python floats and emits full precision.

## Split summary

| Measure | TRAIN | TEST |
|---|---:|---:|
| Observations | 20,631 | 13,096 |
| Units | 100 | 100 |
| Global cycle range | 1–362 | 1–303 |
| Missing values | 0 | 0 |
| Non-finite values | 0 | 0 |
| Duplicate Unit-Cycle keys | 0 | 0 |
| Invalid cycle values | 0 | 0 |
| Missing cycles within each Unit's `1..max` sequence | 0 | 0 |
| Parsing anomalies | 0 | 0 |
| Constant Sensors | 1, 5, 10, 16, 18, 19 | 1, 5, 10, 16, 18, 19 |
| Near-constant Sensors at threshold `1e-4` | none | none |

## TRAIN Sensor statistics

| Sensor | Min | Max | Mean | Population SD | Unique |
|---|---:|---:|---:|---:|---:|
| sensor_1 | 518.67 | 518.67 | 518.67 | 0 | 1 |
| sensor_2 | 641.21 | 644.53 | 642.680934 | 0.500041 | 310 |
| sensor_3 | 1571.04 | 1616.91 | 1590.523119 | 6.131001 | 3012 |
| sensor_4 | 1382.25 | 1441.49 | 1408.933782 | 9.000387 | 4051 |
| sensor_5 | 14.62 | 14.62 | 14.62 | 0 | 1 |
| sensor_6 | 21.60 | 21.61 | 21.609803 | 0.001389 | 2 |
| sensor_7 | 549.85 | 556.06 | 553.367711 | 0.885071 | 513 |
| sensor_8 | 2387.90 | 2388.56 | 2388.096652 | 0.070984 | 53 |
| sensor_9 | 9021.73 | 9244.59 | 9065.242941 | 22.082344 | 6403 |
| sensor_10 | 1.30 | 1.30 | 1.30 | 0 | 1 |
| sensor_11 | 46.85 | 48.53 | 47.541168 | 0.267081 | 159 |
| sensor_12 | 518.69 | 523.38 | 521.413470 | 0.737536 | 427 |
| sensor_13 | 2387.88 | 2388.56 | 2388.096152 | 0.071917 | 56 |
| sensor_14 | 8099.94 | 8293.72 | 8143.752722 | 19.075714 | 6078 |
| sensor_15 | 8.3249 | 8.5848 | 8.442146 | 0.037504 | 1918 |
| sensor_16 | 0.03 | 0.03 | 0.03 | 0 | 1 |
| sensor_17 | 388 | 400 | 393.210654 | 1.548725 | 13 |
| sensor_18 | 2388 | 2388 | 2388 | 0 | 1 |
| sensor_19 | 100 | 100 | 100 | 0 | 1 |
| sensor_20 | 38.14 | 39.43 | 38.816271 | 0.180742 | 120 |
| sensor_21 | 22.8942 | 23.6184 | 23.289705 | 0.108248 | 4745 |

## TEST Sensor statistics

| Sensor | Min | Max | Mean | Population SD | Unique |
|---|---:|---:|---:|---:|---:|
| sensor_1 | 518.67 | 518.67 | 518.67 | 0 | 1 |
| sensor_2 | 641.13 | 644.30 | 642.475088 | 0.400884 | 262 |
| sensor_3 | 1569.04 | 1607.55 | 1588.099204 | 5.003083 | 2361 |
| sensor_4 | 1384.39 | 1433.36 | 1404.735362 | 6.688054 | 2954 |
| sensor_5 | 14.62 | 14.62 | 14.62 | 0 | 1 |
| sensor_6 | 21.60 | 21.61 | 21.609701 | 0.001704 | 2 |
| sensor_7 | 550.88 | 555.84 | 553.757523 | 0.681260 | 415 |
| sensor_8 | 2387.89 | 2388.30 | 2388.070964 | 0.057440 | 41 |
| sensor_9 | 9024.53 | 9155.03 | 9058.407363 | 11.435824 | 4047 |
| sensor_10 | 1.30 | 1.30 | 1.30 | 0 | 1 |
| sensor_11 | 46.80 | 48.26 | 47.416204 | 0.195910 | 136 |
| sensor_12 | 519.38 | 523.76 | 521.747724 | 0.559605 | 357 |
| sensor_13 | 2387.89 | 2388.32 | 2388.071025 | 0.056932 | 43 |
| sensor_14 | 8108.50 | 8220.48 | 8138.947817 | 10.188216 | 3786 |
| sensor_15 | 8.3328 | 8.5414 | 8.425844 | 0.029008 | 1506 |
| sensor_16 | 0.03 | 0.03 | 0.03 | 0 | 1 |
| sensor_17 | 389 | 397 | 392.571625 | 1.233530 | 9 |
| sensor_18 | 2388 | 2388 | 2388 | 0 | 1 |
| sensor_19 | 100 | 100 | 100 | 0 | 1 |
| sensor_20 | 38.31 | 39.41 | 38.892502 | 0.141675 | 103 |
| sensor_21 | 22.9354 | 23.6419 | 23.335743 | 0.084117 | 3555 |

## Operational-setting statistics

| Split | Setting | Min | Max | Mean | Unique |
|---|---|---:|---:|---:|---:|
| TRAIN | setting_1 | -0.0087 | 0.0087 | -0.0000088701 | 158 |
| TRAIN | setting_2 | -0.0006 | 0.0006 | 0.0000023508 | 13 |
| TRAIN | setting_3 | 100 | 100 | 100 | 1 |
| TEST | setting_1 | -0.0082 | 0.0078 | -0.0000111790 | 150 |
| TEST | setting_2 | -0.0006 | 0.0007 | 0.0000042379 | 14 |
| TEST | setting_3 | 100 | 100 | 100 | 1 |

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/m2/m2b/scripts/analyze_fd001_m2b.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2b/tests -v
```

Worker calculations are candidate evidence for Research Brain review; they do not constitute an M2 Gate decision.
