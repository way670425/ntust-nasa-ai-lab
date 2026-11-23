import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  ContractError,
  DATASET_ID,
  SOURCE_TYPE,
  buildEvidencePrompt,
  copyPromptToClipboard,
  evidencePromptIdentity,
  fieldSemanticsFor,
  qualityContextFor,
} from "../state.mjs";
import { M2_QUALITY_METADATA } from "../quality_metadata.mjs";

function makeHistory(split = "TRAIN") {
  const sourceFile = split === "TRAIN" ? "train_FD001.txt" : "test_FD001.txt";
  const sourceHash = M2_QUALITY_METADATA.splits[split].source_sha256;
  return {
    dataset_id: DATASET_ID,
    source_type: SOURCE_TYPE,
    split,
    unit_id: 1,
    sensor: "sensor_7",
    start_cycle: 1,
    end_cycle: 3,
    observation_count: 3,
    observations: [554.36, 553.75, 554.26].map((value, index) => ({
      cycle: index + 1,
      sensor: "sensor_7",
      value,
      source_evidence: {
        source_file: sourceFile,
        source_sha256: sourceHash,
        source_physical_line_1_based: index + 1,
        parsed_row_index_0_based: index,
      },
    })),
  };
}

test("Evidence Prompt maps current OBSERVED identity and selected provenance", () => {
  const prompt = buildEvidencePrompt(makeHistory(), 1);
  assert.match(prompt.text, /\[OBSERVED\]/);
  assert.match(prompt.text, /Dataset ID: NASA_CMAPSS_FD001/);
  assert.match(prompt.text, /Split: TRAIN/);
  assert.match(prompt.text, /Unit ID: 1/);
  assert.match(prompt.text, /Sensor ID: sensor_7/);
  assert.match(prompt.text, /Cycle Range: 1-3/);
  assert.match(prompt.text, /API Observation Count: 3/);
  assert.match(prompt.text, /Selected Cycle: 2/);
  assert.match(prompt.text, /Selected Sensor Value: 553\.75/);
  assert.match(prompt.text, /Source File: train_FD001\.txt/);
  assert.match(prompt.text, /Source Physical Line \(1-based\): 2/);
  assert.match(prompt.text, /Parsed Row Index \(0-based\): 1/);
});

test("DERIVED Mean and Delta state formula, range, N, and reproducible values", () => {
  const prompt = buildEvidencePrompt(makeHistory(), 0);
  assert.match(prompt.text, /\[DERIVED\]/);
  assert.match(prompt.text, /Mean formula: Mean = sum\(values\) \/ N/);
  assert.match(prompt.text, /Calculation source: only the 3 current API observations.*cycles 1-3/);
  assert.match(prompt.text, /Mean calculation: 1662\.37 \/ 3 = 554\.123333/);
  assert.match(prompt.text, /Delta formula: Delta = last - first/);
  assert.match(prompt.text, /Delta calculation: 554\.26 - 554\.36 = -0\.1/);
  assert.equal(prompt.statistics.count, 3);
  assert.ok(Math.abs(prompt.statistics.mean - 554.1233333333333) < 1e-12);
  assert.ok(Math.abs(prompt.statistics.delta - -0.1) < 1e-12);
});

test("Field Semantics maps all accepted Sensor boundaries to one-based source columns", () => {
  assert.equal(fieldSemanticsFor("sensor_1").selected_sensor_source_column_1_based, 6);
  assert.equal(fieldSemanticsFor("sensor_7").selected_sensor_source_column_1_based, 12);
  assert.equal(fieldSemanticsFor("sensor_21").selected_sensor_source_column_1_based, 26);
  assert.throws(() => fieldSemanticsFor("sensor_22"), ContractError);
  const fields = fieldSemanticsFor("sensor_7");
  assert.deepEqual(
    [fields.field_count, fields.unit_fields, fields.cycle_fields, fields.operating_setting_fields, fields.sensor_channels],
    [26, 1, 1, 3, 21],
  );
});

test("Prompt explains 26-field schema, selected Sensor column, units, and Split semantics", () => {
  const trainText = buildEvidencePrompt(makeHistory("TRAIN"), 0).text;
  assert.match(trainText, /26 one-based source fields = 1 Unit ID field \+ 1 Cycle field \+ 3 Operating Settings \+ 21 Sensor Channels/);
  assert.match(trainText, /Selected Sensor Source Column \(one-based\): 12; formula = sensor_number \+ 5/);
  assert.match(trainText, /Selected Sensor Physical Unit: source-defined \/ unspecified/);
  assert.match(trainText, /Do not invent an engineering meaning/);
  assert.match(trainText, /TRAIN is a complete simulated degradation trajectory/);
  const testText = buildEvidencePrompt(makeHistory("TEST"), 0).text;
  assert.match(testText, /TEST is a truncated simulated degradation trajectory; its last observed Cycle is not a failure time/);
  assert.match(testText, /TEST_RUL semantics: independent positional RUL-at-last-observed-Cycle label/);
});

test("Source provenance explanation keeps Physical Line, Parsed Row, and Raw Index distinct", () => {
  const text = buildEvidencePrompt(makeHistory(), 0).text;
  assert.match(text, /Source File is the safe basename/);
  assert.match(text, /Source Physical Line is the actual TXT line number and begins at 1/);
  assert.match(text, /Parsed Row Index is the parsed Observation index within the Split and begins at 0/);
  assert.match(text, /Raw Index means parsed-source traceability coordinates/);
  assert.match(text, /It is not Cycle, failure time, Physical Line, health score/);
});

test("M2 quality context is attributed, exact, Split-level, and not a fault threshold", () => {
  const history = makeHistory("TRAIN");
  const quality = qualityContextFor(history);
  assert.equal(quality.available, true);
  assert.equal(quality.report_source, "research/m2/data_quality_report.md");
  assert.equal(quality.work_item_id, "WO-M2-RESEARCH-001-B");
  assert.equal(quality.scope, "SPLIT_LEVEL");
  assert.equal(quality.observations, 20631);
  assert.equal(quality.units, 100);
  assert.deepEqual(quality.constant_sensors, [1, 5, 10, 16, 18, 19]);
  const text = buildEvidencePrompt(history, 0).text;
  assert.match(text, /this is not Live API quality metadata/);
  assert.match(text, /not statistics for selected Unit 1 or selected Cycles 1-3/);
  assert.match(text, /Constant Sensor finding does not mean Sensor failure/);
  assert.match(text, /statistical threshold is not a warning or fault threshold/);
});

test("TRAIN and TEST quality metadata stay isolated and source-bound", () => {
  const train = qualityContextFor(makeHistory("TRAIN"));
  const testQuality = qualityContextFor(makeHistory("TEST"));
  assert.equal(train.applicable_split, "TRAIN");
  assert.equal(train.observations, 20631);
  assert.equal(testQuality.applicable_split, "TEST");
  assert.equal(testQuality.observations, 13096);
  assert.equal(testQuality.source_file, "test_FD001.txt");
  const mismatched = makeHistory("TRAIN");
  mismatched.observations[0].source_evidence.source_sha256 = "0".repeat(64);
  assert.deepEqual(qualityContextFor(mismatched), {
    available: false,
    status: "UNKNOWN",
    display: "Data quality context unavailable",
  });
  assert.match(buildEvidencePrompt(mismatched, 0).text, /Data quality context unavailable/);
});

test("External AI instructions are complete and implementation performs no external AI request", () => {
  const text = buildEvidencePrompt(makeHistory(), 0).text;
  for (const instruction of [
    "Use only the supplied verified evidence",
    "Preserve the OBSERVED / DERIVED / INFERRED / UNKNOWN classifications",
    "Do not fabricate missing observations",
    "Do not fabricate a baseline, warning threshold, or fault threshold",
    "Do not diagnose engine faults",
    "Do not invent health scores, failure causes, RUL predictions, or RUL values",
    "Do not treat simulated FD001 observations as physical field measurements",
    "local copy only",
  ]) assert.match(text, new RegExp(instruction.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"));
  const appSource = readFileSync(new URL("../app.js", import.meta.url), "utf8");
  assert.doesNotMatch(appSource, /https?:\/\//i);
  assert.doesNotMatch(appSource, /openai|anthropic|gemini|external ai sdk/i);
  assert.match(appSource, /fetch\(path/);
});

test("INFERRED and UNKNOWN classifications keep conclusions bounded", () => {
  const text = buildEvidencePrompt(makeHistory(), 0).text;
  assert.match(text, /\[INFERRED\]/);
  assert.match(text, /No verified fault, failure, anomaly, or failure cause is supported/);
  assert.match(text, /\[UNKNOWN\]/);
  assert.match(text, /Physical engine condition: unknown/);
  assert.match(text, /Health score: unknown/);
  assert.match(text, /RUL prediction\/value for this query: unknown/);
});

test("required simulation, TRAIN, TEST, TEST_RUL, and diagnosis disclosures are present", () => {
  const text = buildEvidencePrompt(makeHistory(), 0).text;
  assert.match(text, /simulated turbofan degradation dataset/);
  assert.match(text, /not physical equipment field measurement/);
  assert.match(text, /TRAIN contains simulated complete degradation trajectories/);
  assert.match(text, /TEST contains truncated simulated trajectories/);
  assert.match(text, /last observed Cycle is not a failure time/);
  assert.match(text, /TEST_RUL is an independent label at the last observed Cycle, not a Sensor Observation/);
  assert.match(text, /Sensor trend and derived statistics are not a verified fault diagnosis/);
  assert.match(text, /Do not insert an RUL value unless a validated API response explicitly provides it/);
});

test("Split isolation and selected-observation changes produce new prompt identities", () => {
  const train = makeHistory("TRAIN");
  const testHistory = makeHistory("TEST");
  const trainPrompt = buildEvidencePrompt(train, 0);
  const selectedPrompt = buildEvidencePrompt(train, 2);
  const testPrompt = buildEvidencePrompt(testHistory, 0);
  assert.notEqual(trainPrompt.identity, selectedPrompt.identity);
  assert.notEqual(trainPrompt.identity, testPrompt.identity);
  assert.match(testPrompt.text, /Split: TEST/);
  assert.match(testPrompt.text, /Source File: test_FD001\.txt/);
  assert.doesNotMatch(testPrompt.text, /Source File: train_FD001\.txt/);
});

test("invalid and null Prompt sources are rejected", () => {
  assert.throws(() => buildEvidencePrompt(null, 0), ContractError);
  assert.throws(() => buildEvidencePrompt(makeHistory(), 99), ContractError);
  const invalid = makeHistory();
  invalid.observations[1].value = null;
  assert.throws(() => buildEvidencePrompt(invalid, 1), ContractError);
});

test("Prompt contains no fabricated diagnosis, numeric threshold, baseline, health score, or RUL", () => {
  const text = buildEvidencePrompt(makeHistory(), 0).text;
  assert.doesNotMatch(text, /confirmed fault diagnosis/i);
  assert.doesNotMatch(text, /known failure cause/i);
  assert.doesNotMatch(text, /(warning|failure) threshold:\s*[-+]?\d/i);
  assert.doesNotMatch(text, /health score:\s*[-+]?\d/i);
  assert.doesNotMatch(text, /RUL(?: prediction| value)?:\s*[-+]?\d/i);
  assert.doesNotMatch(text, /baseline:\s*[-+]?\d/i);
});

test("copy interaction writes exactly the visible current Prompt", async () => {
  const history = makeHistory();
  const prompt = buildEvidencePrompt(history, 1);
  let clipboardValue = null;
  let writes = 0;
  const clipboard = { async writeText(value) { clipboardValue = value; writes += 1; } };
  const copied = await copyPromptToClipboard(prompt, prompt.text, prompt.identity, clipboard);
  assert.equal(copied, prompt.text);
  assert.equal(clipboardValue, prompt.text);
  assert.equal(writes, 1);
});

test("stale, altered, unavailable, and failed Clipboard writes never report success", async () => {
  const history = makeHistory();
  const prompt = buildEvidencePrompt(history, 0);
  let writes = 0;
  const clipboard = { async writeText() { writes += 1; } };
  await assert.rejects(copyPromptToClipboard(prompt, `${prompt.text} altered`, prompt.identity, clipboard), ContractError);
  await assert.rejects(copyPromptToClipboard(prompt, prompt.text, evidencePromptIdentity(history, 1), clipboard), ContractError);
  await assert.rejects(copyPromptToClipboard(prompt, prompt.text, prompt.identity, null), ContractError);
  await assert.rejects(
    copyPromptToClipboard(prompt, prompt.text, prompt.identity, { async writeText() { throw new Error("denied"); } }),
    /denied/,
  );
  assert.equal(writes, 0);
});
