# M2 FD001 Validation — Public Research Summary

Work item: `WO-M2-RESEARCH-001`

Status: Worker validation evidence completed; M2 Gate review remains pending. This publication does not declare Research Brain or MAIN acceptance.

## Scope

This branch publishes reproducible validation methods and aggregate results for the locally accepted FD001 source files. Per project governance, local source trust was accepted by the student for this M2; an external chain-of-custody check was not required.

No raw dataset file, full raw-row index, complete source excerpt, private absolute path, credential, or secret is included.

## M2-A results

| Check | Train | Test | RUL |
|---|---:|---:|---:|
| Rows | 20,631 | 13,096 | 100 |
| Effective columns | 26 | 26 | 1 |
| Units | 100 | 100 | 100 positional labels |
| Unit IDs | 1–100 | 1–100 | line N maps to Test Unit N |
| Global cycle range | 1–362 | 1–303 | not applicable |
| Operational-setting fields | 3 | 3 | not applicable |
| Sensor fields | 21 | 21 | not applicable |
| Missing/invalid values | 0 | 0 | 0 |
| Duplicate Unit-Cycle keys | 0 | 0 | not applicable |

Independent full-row validation checked all 33,727 Train/Test observations plus all 100 RUL labels. Schema, Raw Index alignment, Unit/Cycle integrity, operational settings, sensor fields, and RUL mapping each passed with zero failures.

## Source identity

Only hashes are published; source files themselves are excluded.

```text
train_FD001.txt  963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8
test_FD001.txt   3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851
RUL_FD001.txt    a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca
```

The RUL file is a positional label vector: physical line N (1-based) maps to Test Unit N. It is not a sensor observation table.

## Reproduction

The scripts expect the read-only source files under `data/FD001/`. Generated indexes and summaries remain local and must not be committed.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2a/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 research/m2/data_validation/scripts/validate_m2a_gate.py
```

Observed results:

- Existing tests: 6/6 passed.
- Independent Data Validation Gate: overall `PASS`.
- Failed source rows: 0.
- Source hashes were unchanged before and after validation.

Worker test success is evidence only and does not constitute an M2 Gate PASS.

## Published files

- `research/m2/m2a/scripts/verify_fd001_m2a.py`
- `research/m2/m2a/tests/test_verify_fd001_m2a.py`
- `research/m2/data_validation/scripts/validate_m2a_gate.py`
- `research/m2/public/m2a_validation_summary.json`
- this summary

## Explicit exclusions

- `train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt`
- `synthetic_sensor.csv`
- full Raw Index CSV files
- local summary/evidence bundles containing absolute paths or source-row excerpts
- full or reconstructable raw sensor rows
- unrelated M0, M1, and Web work

## Phase boundary

The following remain `NOT_COMPLETED` and require separate authorization:

- Data Quality Summary
- Cycle-based Sensor Trend Analysis
- FD001 Data Contract

No Phase C/D work was started for this GitHub delivery.
