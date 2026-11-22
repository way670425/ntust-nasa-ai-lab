# M2-B R1 Root Cause Report

Work item: `WO-M2-RESEARCH-001-B-R1`
Parent: `WO-M2-RESEARCH-001-B`
Base commit: `2ad5d1786c37cb35b904f9ce0ffe2014b85c32cc`

## Investigation protocol

Before changing any file, the Worker ran:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/m2/m2b/tests -p 'test_data_contract.py' -v
```

Original result: 4 tests run; 2 passed and 2 failed; exit code 1. The original console output and complete Python tracebacks were preserved in the WO-M2-RESEARCH-001-B-R1 execution transcript before any edit.

## Failure 1 — SIMULATION_WORDING_ASSERTION_FAILURE

- Test name: `test_safety_semantics`
- Test file: `research/m2/m2b/tests/test_data_contract.py`
- Original test line: 54 (assertion), with required token at original line 50
- Original assertion: `self.assertIn(required, self.text)` while `required == "模擬"`
- Expected: the literal Chinese token `模擬` appears in the Contract.
- Actual: Contract line 9 used English `simulated` and stated that the data was not physical field measurement data, but did not contain the literal Chinese token.
- Contract location before fix: `research/m2/data_contract.md`, line 9, Identity and scope.
- Root cause classification: `BOTH`

Original traceback:

```text
Traceback (most recent call last):
  File "research/m2/m2b/tests/test_data_contract.py", line 54, in test_safety_semantics
    self.assertIn(required, self.text)
AssertionError: '模擬' not found in <the complete pre-fix FD001 Data Contract text printed by unittest>
```

The original assertion was too narrow because it validated one token rather than the full semantics. The Contract already said `simulated` and excluded physical field measurements, but R1 additionally requires explicit statements that the local files are student-trusted and that unverified equipment faults or RUL predictions must not be claimed.

Minimal correction:

1. Contract Identity and scope now states all four required semantics explicitly.
2. The test now checks the four complete phrases, while retaining the existing TEST/RUL, non-physical-data and no-Web-API safety checks.

## Failure 2 — SENSOR_NAME_REGEX_COUNT_FAILURE

- Test name: `test_schema_and_traceability_fields`
- Test file: `research/m2/m2b/tests/test_data_contract.py`
- Original test line: 44
- Original assertion: `self.assertEqual(len(sensor_fields), 21)`
- Original Regex: `sensor_(?:[1-9]|1[0-9]|2[01])`
- Expected: 21 unique formal fields, exactly `sensor_1` through `sensor_21`.
- Actual: 25 matches but only 9 unique strings: `sensor_1` through `sensor_9`.
- Contract location: `research/m2/data_contract.md`, original lines 33–53, Observation schema.
- Root cause classification: `TEST_ASSERTION_DEFECT`

Original traceback:

```text
Traceback (most recent call last):
  File "research/m2/m2b/tests/test_data_contract.py", line 44, in test_schema_and_traceability_fields
    self.assertEqual(len(sensor_fields), 21)
AssertionError: 9 != 21
```

Original Regex matches in order:

```text
sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6, sensor_7, sensor_8, sensor_9,
sensor_1, sensor_1, sensor_1, sensor_1, sensor_1, sensor_1, sensor_1, sensor_1, sensor_1,
sensor_1, sensor_2, sensor_2, sensor_1, sensor_2, sensor_1, sensor_2
```

The alternation tried `[1-9]` first, so it truncated `sensor_10`–`sensor_19` to `sensor_1` and `sensor_20`–`sensor_21` to `sensor_2`. The Contract schema itself correctly listed all 21 fields exactly once.

Minimal correction:

- Match only Markdown schema rows anchored at line start.
- Capture longer numeric alternatives first: `2[01]|1[0-9]|[1-9]`.
- Assert total count 21, unique count 21 and exact set equality with `sensor_1` through `sensor_21`.
- Assert that `operating_setting` is not among the captured Sensor fields.

## Scope statement

No M2-A parser, Raw Index, analysis formula, quality statistic, trend value, source file, Web artifact, M0 artifact or M1 artifact was changed by this rework.
