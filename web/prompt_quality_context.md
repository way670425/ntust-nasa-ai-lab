# FD001 Prompt Quality Context Integration

- Work item: `WO-M4-WEB-PROMPT-ENHANCE-001`
- Metadata module: `web/frontend/quality_metadata.mjs`
- Metadata version: `WO-M2-RESEARCH-001-B/v1`
- Research source: `research/m2/data_quality_report.md`
- Contract source: `research/m2/data_contract.md`
- Scope: `SPLIT_LEVEL`

The web Metadata is a versioned transcription of accepted M2 report values. It is not returned by the live M3-A API and is never described as current-Unit or current-range evidence. At runtime it is available only when dataset ID, source type, Split, safe source basename and every current observation's source SHA-256 match the accepted Metadata. Otherwise the Prompt states `Data quality context unavailable` with status `UNKNOWN`.

## Verified transcription

| Field | TRAIN | TEST |
|---|---:|---:|
| Source file | `train_FD001.txt` | `test_FD001.txt` |
| SHA-256 | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` |
| Observations | 20,631 | 13,096 |
| Units | 100 | 100 |
| Missing values | 0 | 0 |
| Non-finite values | 0 | 0 |
| Duplicate Unit-Cycle | 0 | 0 |
| Invalid Cycle | 0 | 0 |
| Missing Cycles | 0 | 0 |
| Parsing anomalies | 0 | 0 |
| Constant Sensors | 1, 5, 10, 16, 18, 19 | 1, 5, 10, 16, 18, 19 |
| Near-constant Sensors | NONE | NONE |

Near-constant method: non-constant and `(max-min)/max(abs(min),abs(max),1) <= 1e-4`. The Prompt explicitly says this statistical threshold is not a warning or fault threshold and a Constant Sensor finding is not Sensor failure.

`TEST_RUL` remains a separate positional label source with accepted SHA-256 `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca`. It is not a per-Cycle Sensor Observation and no RUL value is inserted into the Prompt.

## Field semantics

The accepted source schema has 26 one-based fields: Unit ID at 1, Cycle at 2, three Operating Settings at 3–5, and 21 Sensor channels at 6–26. Selected Sensor source column is `sensor_number + 5`; therefore sensor_1=6, sensor_7=12 and sensor_21=26. Physical units and engineering meanings remain source-defined/unspecified.

No Research document, M3-A API/Loader, raw source or Raw Index publication was modified or copied into the web artifacts.
