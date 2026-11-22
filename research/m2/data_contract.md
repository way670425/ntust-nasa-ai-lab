# FD001 Data Contract

Work item: `WO-M2-RESEARCH-001-B`

## Identity and scope

- `dataset_id`: `NASA_CMAPSS_FD001`
- `source_type`: `NASA_FD001_LOCAL_TRUSTED`
- Data semantics: NASA C-MAPSS FD001 是模擬引擎退化資料集；本研究使用學生已信任的本地 FD001 檔案。模擬資料不等於實體引擎現場量測，也不是實體設備實測資料；不得聲稱未經證實的設備故障或 RUL 預測。
- Contract scope: a read/query interface for future Web work. This work item does not implement a Web API（不實作 Web API）.

## Splits

| Split | Source | Semantics |
|---|---|---|
| `TRAIN` | `train_FD001.txt` | Complete simulated run-to-failure trajectories according to the accepted dataset semantics. |
| `TEST` | `test_FD001.txt` | Truncated simulated trajectories. The final observed cycle must not be treated as a failure time（不得視為故障時刻）. |
| `TEST_RUL` | `RUL_FD001.txt` | One positional label per TEST Unit: `rul_at_last_observed_cycle`. It is not a Sensor Observation（不是 Sensor Observation）. |

TRAIN Unit 1 and TEST Unit 1 belong to different split-scoped populations. The stable identity is `(dataset_id, split, unit_id)`, not `unit_id` alone.

## Observation schema

Every TRAIN or TEST physical line has 26 whitespace-delimited fields in this order:

| Field | Type | Unit | Nullable | Query semantics |
|---|---|---|:---:|---|
| `unit_id` | integer | none | no | Positive split-scoped engine identifier. |
| `cycle` | integer | cycle | no | Positive observation sequence within a Unit; begins at 1 and is contiguous in the accepted source. |
| `setting_1` | number | source-defined/unspecified | no | Operational setting 1. |
| `setting_2` | number | source-defined/unspecified | no | Operational setting 2. |
| `setting_3` | number | source-defined/unspecified | no | Operational setting 3. |
| `sensor_1` | number | source-defined/unspecified | no | Sensor channel 1. |
| `sensor_2` | number | source-defined/unspecified | no | Sensor channel 2. |
| `sensor_3` | number | source-defined/unspecified | no | Sensor channel 3. |
| `sensor_4` | number | source-defined/unspecified | no | Sensor channel 4. |
| `sensor_5` | number | source-defined/unspecified | no | Sensor channel 5. |
| `sensor_6` | number | source-defined/unspecified | no | Sensor channel 6. |
| `sensor_7` | number | source-defined/unspecified | no | Sensor channel 7. |
| `sensor_8` | number | source-defined/unspecified | no | Sensor channel 8. |
| `sensor_9` | number | source-defined/unspecified | no | Sensor channel 9. |
| `sensor_10` | number | source-defined/unspecified | no | Sensor channel 10. |
| `sensor_11` | number | source-defined/unspecified | no | Sensor channel 11. |
| `sensor_12` | number | source-defined/unspecified | no | Sensor channel 12. |
| `sensor_13` | number | source-defined/unspecified | no | Sensor channel 13. |
| `sensor_14` | number | source-defined/unspecified | no | Sensor channel 14. |
| `sensor_15` | number | source-defined/unspecified | no | Sensor channel 15. |
| `sensor_16` | number | source-defined/unspecified | no | Sensor channel 16. |
| `sensor_17` | number | source-defined/unspecified | no | Sensor channel 17. |
| `sensor_18` | number | source-defined/unspecified | no | Sensor channel 18. |
| `sensor_19` | number | source-defined/unspecified | no | Sensor channel 19. |
| `sensor_20` | number | source-defined/unspecified | no | Sensor channel 20. |
| `sensor_21` | number | source-defined/unspecified | no | Sensor channel 21. |

All numeric values must be finite. A missing, malformed, null, or non-finite required field rejects the source row; the implementation must not silently impute it.

## Source evidence fields

Every returned observation must preserve:

| Field | Type | Nullable | Meaning |
|---|---|:---:|---|
| `source_file` | string | no | Source basename, not a private absolute path. |
| `source_sha256` | 64-character lowercase hex string | no | SHA-256 of the complete local source file. |
| `source_physical_line_1_based` | integer | no | Physical source line beginning at 1. |
| `parsed_row_index_0_based` | integer | no | Parsed split row index beginning at 0. |

Accepted SHA-256 values:

- `train_FD001.txt`: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- `test_FD001.txt`: `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851`
- `RUL_FD001.txt`: `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca`

## TEST_RUL mapping

`RUL_FD001.txt` physical line `N` (1-based) maps positionally to TEST `unit_id=N`; parsed row index is `N-1`. Its value is an integer `rul_at_last_observed_cycle` for that TEST Unit. It must not be expanded as if it were a per-cycle Sensor value, and it must not be attached to TRAIN rows.

## Validation preconditions

Before data is queryable:

1. Source SHA-256 must match the accepted values above.
2. TRAIN and TEST must each have exactly 26 effective fields per physical line.
3. The schema must contain one Unit field, one cycle field, three settings, and 21 Sensors in the declared order.
4. `unit_id` and `cycle` must be positive integers; setting and Sensor values must be finite numbers.
5. `(split, unit_id, cycle)` must be unique.
6. Each Unit's cycles must be contiguous from 1 in source order.
7. Source physical line and parsed row index must remain aligned and traceable.
8. TEST_RUL must contain exactly one non-negative integer label per TEST Unit and satisfy the positional mapping.
9. TRAIN and TEST must never be joined by `unit_id` alone.

Any failed precondition blocks publication and query service; raw source data must not be modified to make validation pass.

## Suggested JSON query response

```json
{
  "dataset_id": "NASA_CMAPSS_FD001",
  "source_type": "NASA_FD001_LOCAL_TRUSTED",
  "split": "TEST",
  "unit_id": 1,
  "cycle": 1,
  "settings": {
    "setting_1": 0.0023,
    "setting_2": 0.0003,
    "setting_3": 100.0
  },
  "sensors": {
    "sensor_1": 518.67,
    "sensor_2": 643.02
  },
  "source_evidence": {
    "source_file": "test_FD001.txt",
    "source_sha256": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
    "source_physical_line_1_based": 1,
    "parsed_row_index_0_based": 0
  },
  "rul_at_last_observed_cycle": 112
}
```

The example is a traceable subset, not a complete raw row. `rul_at_last_observed_cycle` is nullable for queries where the split is not TEST or the label was not requested. Sensor keys may be filtered by an explicit Sensor selection, but every returned key must retain its declared name and numeric type.

## Query rules and errors

- Required selectors: `split` in `TRAIN|TEST`, positive `unit_id`, optional positive `cycle`, and Sensor names matching `sensor_1` through `sensor_21`.
- An omitted cycle means the caller explicitly requests the Unit's available cycle range; it must not imply the final cycle is failure.
- Unknown split: HTTP-style status `400`, code `INVALID_SPLIT`.
- Unknown Sensor name: `400`, code `INVALID_SENSOR`.
- Non-positive or non-integer Unit/cycle: `400`, code `INVALID_QUERY_VALUE`.
- Valid but absent Unit or cycle: `404`, code `OBSERVATION_NOT_FOUND`.
- Source validation failure: `503`, code `SOURCE_NOT_VALIDATED`; no partial data response.
- Error bodies should include `code`, `message`, and normalized query fields, but never private absolute paths or raw source lines.

## Publication boundary

GitHub may contain this contract, validation code, aggregate statistics, selected safe traceability examples, and hashes. It must not contain NASA source files, complete Raw Index files, large reconstructable row collections, private absolute paths, credentials, or secrets.
