# M2-B R1 Worker Execution Report

- Work item: `WO-M2-RESEARCH-001-B-R1`
- Worker: Codex
- Base commit: `2ad5d1786c37cb35b904f9ce0ffe2014b85c32cc`
- Branch: `main`
- Return to: STUDENT-RESEARCH Brain
- Worker status: `SUCCESS_CANDIDATE_PENDING_RESEARCH_BRAIN_REVIEW`

## Root causes and minimal fixes

1. Simulation wording: `BOTH`. The Contract used English `simulated` and excluded physical field measurements, but did not contain every explicit R1 semantic. The original test checked only a single Chinese token. The Contract now states all required semantics, and the test validates the complete phrases.
2. Sensor name Regex: `TEST_ASSERTION_DEFECT`. The Contract already listed exactly 21 formal Sensor fields. The original alternation matched the short numeric branch first. The fixed test anchors matches to formal Markdown schema rows, uses longer alternatives first, and verifies count, uniqueness and exact set equality.

Detailed pre-fix assertions, actual results, tracebacks, line locations and original Regex matches are recorded in `research/m2/m2b_rework_root_cause_report.md` and the execution transcript.

## Regression evidence

| Check | Command | Result | Exit code |
|---|---|---|---:|
| M2-A existing tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2a/tests -v` | 6/6 PASS | 0 |
| M2-A full-row validation | `PYTHONDONTWRITEBYTECODE=1 python3 research/m2/data_validation/scripts/validate_m2a_gate.py` | Overall PASS; six Gates passed with zero failures | 0 |
| M2-B all tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2b/tests -v` | 10/10 PASS | 0 |
| Contract validation | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2b/tests -p 'test_data_contract.py' -v` | 4/4 PASS | 0 |
| Source integrity | `shasum -a 256 data/FD001/train_FD001.txt data/FD001/test_FD001.txt data/FD001/RUL_FD001.txt` | All accepted SHA-256 values matched | 0 |

M2-A full-row validation covered 20,631 TRAIN observations, 13,096 TEST observations and 100 TEST_RUL labels. Schema, Raw Index, Unit/Cycle, setting, Sensor and RUL mapping Gates each reported zero failures.

## Source integrity

- `train_FD001.txt`: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- `test_FD001.txt`: `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851`
- `RUL_FD001.txt`: `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca`

The original files were read only for validation and analysis; no source value was modified.

## Publication boundary

Candidate publication contains only M2-B methods, tests, aggregate quality statistics, six bounded trend examples, the formal Contract, root-cause evidence and Worker reports. It excludes source datasets, synthetic CSV, complete Raw Index files, private absolute paths, secrets, tokens, passwords, bulk Sensor rows and unrelated Web/M0/M1 changes.

Worker success is execution evidence only. It does not constitute Research PASS or M2 Gate PASS.
