import test from "node:test";
import assert from "node:assert/strict";

import {
  ContractError,
  DATASET_ID,
  SOURCE_TYPE,
  RequestGate,
  errorLabel,
  evidenceFor,
  mapHistory,
  parseCatalog,
  parseHealth,
  parseHistory,
  parseUnits,
  refreshForSensor,
  resetForSplit,
  resetForUnit,
  validateCycleRange,
} from "../state.mjs";

const catalog = {
  dataset_id: DATASET_ID,
  source_type: SOURCE_TYPE,
  available_splits: ["TRAIN", "TEST"],
  sensor_names: Array.from({ length: 21 }, (_, index) => `sensor_${index + 1}`),
};

const query = { split: "TRAIN", unit: 1, sensor: "sensor_7", start: 1, end: 2 };
const history = {
  dataset_id: DATASET_ID,
  source_type: SOURCE_TYPE,
  split: "TRAIN",
  unit_id: 1,
  sensor: "sensor_7",
  start_cycle: 1,
  end_cycle: 2,
  observation_count: 2,
  observations: [
    {
      cycle: 1,
      sensor: "sensor_7",
      value: 554.36,
      source_evidence: {
        source_file: "train_FD001.txt",
        source_sha256: "9".repeat(64),
        source_physical_line_1_based: 1,
        parsed_row_index_0_based: 0,
      },
    },
    {
      cycle: 2,
      sensor: "sensor_7",
      value: 553.75,
      source_evidence: {
        source_file: "train_FD001.txt",
        source_sha256: "9".repeat(64),
        source_physical_line_1_based: 2,
        parsed_row_index_0_based: 1,
      },
    },
  ],
};

test("parses validated API health, Catalog, Units, and History", () => {
  assert.equal(parseHealth({ status: "ok", dataset_id: DATASET_ID, source_type: SOURCE_TYPE, data_validated: true, read_only: true }).data_validated, true);
  assert.equal(parseCatalog(catalog).sensor_names.length, 21);
  assert.deepEqual(
    parseUnits({ dataset_id: DATASET_ID, source_type: SOURCE_TYPE, split: "TRAIN", units: [{ unit_id: 1, min_cycle: 1, max_cycle: 2, observation_count: 2 }] }, "TRAIN"),
    [{ unit_id: 1, min_cycle: 1, max_cycle: 2, observation_count: 2 }],
  );
  assert.equal(parseHistory(history, query).observations[0].value, 554.36);
});

test("selector state resets prevent stale Split, Unit, and Sensor data", () => {
  const populated = { split: "TRAIN", unit: { unit_id: 1 }, units: [{ unit_id: 1 }], sensor: "sensor_7", start: 1, end: 20, history, selectedIndex: 0 };
  const splitState = resetForSplit(populated, "TEST");
  assert.equal(splitState.split, "TEST");
  assert.equal(splitState.unit, null);
  assert.equal(splitState.history, null);
  assert.deepEqual(splitState.units, []);

  const unitState = resetForUnit(splitState, { unit_id: 2, min_cycle: 1, max_cycle: 10 });
  assert.equal(unitState.unit.unit_id, 2);
  assert.equal(unitState.end, 10);
  assert.equal(unitState.selectedIndex, null);

  const sensorState = refreshForSensor({ ...unitState, history }, "sensor_8");
  assert.equal(sensorState.sensor, "sensor_8");
  assert.equal(sensorState.history, null);
});

test("cycle range validation rejects invalid, reversed, and out-of-range inputs", () => {
  const unit = { min_cycle: 1, max_cycle: 31 };
  assert.deepEqual(validateCycleRange("1", "20", unit), { valid: true, start: 1, end: 20 });
  assert.equal(validateCycleRange("0", "20", unit).valid, false);
  assert.equal(validateCycleRange("2", "1", unit).valid, false);
  assert.equal(validateCycleRange("1", "32", unit).valid, false);
  assert.equal(validateCycleRange("1.5", "2", unit).valid, false);
});

test("trend, table, and evidence mappings stay observation-consistent", () => {
  const parsed = parseHistory(history, query);
  const mapped = mapHistory(parsed);
  assert.deepEqual(mapped.points.map(({ cycle, value }) => ({ cycle, value })), [{ cycle: 1, value: 554.36 }, { cycle: 2, value: 553.75 }]);
  assert.equal(mapped.rows[1].source_evidence.source_physical_line_1_based, 2);
  assert.deepEqual(mapped.points.map((point) => point.index), mapped.rows.map((row) => row.index));
  assert.equal(evidenceFor(parsed, 1).parsed_row_index_0_based, 1);
  assert.equal(evidenceFor(parsed, 99), null);
});

test("null, non-finite, unsafe provenance, and mismatched responses are rejected", () => {
  for (const value of [null, Number.NaN, Number.POSITIVE_INFINITY]) {
    const invalid = structuredClone(history);
    invalid.observations[0].value = value;
    assert.throws(() => parseHistory(invalid, query), ContractError);
  }
  const unsafe = structuredClone(history);
  unsafe.observations[0].source_evidence.source_file = "/private/train_FD001.txt";
  assert.throws(() => parseHistory(unsafe, query), ContractError);
  assert.throws(() => parseHistory({ ...history, split: "TEST" }, query), ContractError);
});

test("HTTP status mapping uses the required safe UI labels", () => {
  assert.equal(errorLabel(400), "Query Validation Error");
  assert.equal(errorLabel(404), "Observation Not Found");
  assert.equal(errorLabel(503), "Source Not Validated");
  assert.equal(errorLabel(502), "Connection Error");
});

test("request identity and AbortController prevent stale responses", () => {
  const gate = new RequestGate();
  const first = gate.begin();
  const second = gate.begin();
  assert.equal(first.signal.aborted, true);
  assert.equal(gate.isCurrent(first.identity), false);
  assert.equal(gate.isCurrent(second.identity), true);
  gate.cancel();
  assert.equal(second.signal.aborted, true);
  assert.equal(gate.isCurrent(second.identity), false);
});
