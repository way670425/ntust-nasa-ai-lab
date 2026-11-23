import test from "node:test";
import assert from "node:assert/strict";

import {
  ContractError,
  DATASET_ID,
  SOURCE_TYPE,
  buildEvidencePrompt,
  copyPromptToClipboard,
  evidencePromptIdentity,
} from "../state.mjs";

function makeHistory(split = "TRAIN") {
  const sourceFile = split === "TRAIN" ? "train_FD001.txt" : "test_FD001.txt";
  const sourceHash = split === "TRAIN" ? "9".repeat(64) : "3".repeat(64);
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
