export const DATASET_ID = "NASA_CMAPSS_FD001";
export const SOURCE_TYPE = "NASA_FD001_LOCAL_TRUSTED";

export class ContractError extends Error {}

function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ContractError(`${label} must be an object`);
  }
  return value;
}

function requireString(value, label) {
  if (typeof value !== "string" || value.length === 0) {
    throw new ContractError(`${label} must be a non-empty string`);
  }
  return value;
}

function requirePositiveInteger(value, label) {
  if (!Number.isInteger(value) || value <= 0) {
    throw new ContractError(`${label} must be a positive integer`);
  }
  return value;
}

export function parseHealth(payload) {
  const body = requireObject(payload, "health response");
  if (
    body.status !== "ok" ||
    body.dataset_id !== DATASET_ID ||
    body.source_type !== SOURCE_TYPE ||
    body.data_validated !== true ||
    body.read_only !== true
  ) {
    throw new ContractError("Source health response is not validated and read-only");
  }
  return body;
}

export function parseCatalog(payload) {
  const body = requireObject(payload, "catalog response");
  if (body.dataset_id !== DATASET_ID || body.source_type !== SOURCE_TYPE) {
    throw new ContractError("Catalog source identity does not match FD001");
  }
  if (!Array.isArray(body.available_splits) || !body.available_splits.includes("TRAIN") || !body.available_splits.includes("TEST")) {
    throw new ContractError("Catalog must include TRAIN and TEST splits");
  }
  if (!Array.isArray(body.sensor_names) || body.sensor_names.length !== 21) {
    throw new ContractError("Catalog must include 21 Sensor channels");
  }
  const expectedSensors = Array.from({ length: 21 }, (_, index) => `sensor_${index + 1}`);
  if (body.sensor_names.some((sensor, index) => sensor !== expectedSensors[index])) {
    throw new ContractError("Catalog Sensor order is invalid");
  }
  return {
    ...body,
    available_splits: [...body.available_splits],
    sensor_names: [...body.sensor_names],
  };
}

export function parseUnits(payload, expectedSplit) {
  const body = requireObject(payload, "units response");
  if (body.dataset_id !== DATASET_ID || body.source_type !== SOURCE_TYPE || body.split !== expectedSplit) {
    throw new ContractError("Unit response identity does not match the requested split");
  }
  if (!Array.isArray(body.units) || body.units.length === 0) {
    throw new ContractError("Unit response is empty");
  }
  return body.units.map((raw, index) => {
    const unit = requireObject(raw, `unit ${index}`);
    const unitId = requirePositiveInteger(unit.unit_id, "unit_id");
    const minCycle = requirePositiveInteger(unit.min_cycle, "min_cycle");
    const maxCycle = requirePositiveInteger(unit.max_cycle, "max_cycle");
    const count = requirePositiveInteger(unit.observation_count, "observation_count");
    if (minCycle > maxCycle || count !== maxCycle - minCycle + 1) {
      throw new ContractError("Unit cycle range is inconsistent");
    }
    return { unit_id: unitId, min_cycle: minCycle, max_cycle: maxCycle, observation_count: count };
  });
}

function safeSourceFile(value) {
  const sourceFile = requireString(value, "source_file");
  if (sourceFile.includes("/") || sourceFile.includes("\\")) {
    throw new ContractError("source_file must be a safe basename");
  }
  return sourceFile;
}

export function parseHistory(payload, query) {
  const body = requireObject(payload, "history response");
  if (
    body.dataset_id !== DATASET_ID ||
    body.source_type !== SOURCE_TYPE ||
    body.split !== query.split ||
    body.unit_id !== query.unit ||
    body.sensor !== query.sensor ||
    body.start_cycle !== query.start ||
    body.end_cycle !== query.end
  ) {
    throw new ContractError("History response does not match the active query");
  }
  if (!Array.isArray(body.observations) || body.observations.length === 0) {
    throw new ContractError("History response has no observations");
  }
  if (body.observation_count !== body.observations.length) {
    throw new ContractError("History observation count is inconsistent");
  }

  let previousCycle = 0;
  const observations = body.observations.map((raw, index) => {
    const observation = requireObject(raw, `observation ${index}`);
    const cycle = requirePositiveInteger(observation.cycle, "cycle");
    if (cycle <= previousCycle || cycle < query.start || cycle > query.end) {
      throw new ContractError("Observation cycles are not strictly increasing within the query range");
    }
    previousCycle = cycle;
    if (observation.sensor !== query.sensor) {
      throw new ContractError("Observation Sensor does not match the active query");
    }
    if (typeof observation.value !== "number" || !Number.isFinite(observation.value)) {
      throw new ContractError("Observation value must be a finite non-null number");
    }
    const evidence = requireObject(observation.source_evidence, "source_evidence");
    const sourceSha = requireString(evidence.source_sha256, "source_sha256");
    if (!/^[0-9a-f]{64}$/.test(sourceSha)) {
      throw new ContractError("source_sha256 is invalid");
    }
    const physicalLine = requirePositiveInteger(
      evidence.source_physical_line_1_based,
      "source_physical_line_1_based",
    );
    if (!Number.isInteger(evidence.parsed_row_index_0_based) || evidence.parsed_row_index_0_based < 0) {
      throw new ContractError("parsed_row_index_0_based is invalid");
    }
    return {
      cycle,
      sensor: observation.sensor,
      value: observation.value,
      source_evidence: {
        source_file: safeSourceFile(evidence.source_file),
        source_sha256: sourceSha,
        source_physical_line_1_based: physicalLine,
        parsed_row_index_0_based: evidence.parsed_row_index_0_based,
      },
    };
  });
  return { ...body, observations };
}

export function validateCycleRange(startInput, endInput, unit) {
  const start = Number(startInput);
  const end = Number(endInput);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start <= 0 || end <= 0) {
    return { valid: false, message: "Cycles must be positive integers." };
  }
  if (start > end) {
    return { valid: false, message: "Start Cycle cannot exceed End Cycle." };
  }
  if (!unit || start < unit.min_cycle || end > unit.max_cycle) {
    return { valid: false, message: "Cycle range is outside the selected Unit." };
  }
  return { valid: true, start, end };
}

export function resetForSplit(state, split) {
  return {
    ...state,
    split,
    unit: null,
    units: [],
    start: null,
    end: null,
    history: null,
    selectedIndex: null,
    prompt: null,
  };
}

export function resetForUnit(state, unit) {
  const start = unit.min_cycle;
  const end = Math.min(unit.max_cycle, start + 19);
  return { ...state, unit, start, end, history: null, selectedIndex: null, prompt: null };
}

export function refreshForSensor(state, sensor) {
  return { ...state, sensor, history: null, selectedIndex: null, prompt: null };
}

export function mapHistory(history) {
  const points = history.observations.map((observation, index) => ({
    index,
    cycle: observation.cycle,
    value: observation.value,
  }));
  const rows = history.observations.map((observation, index) => ({ index, ...observation }));
  return { points, rows };
}

export function evidenceFor(history, index) {
  const observation = history?.observations?.[index];
  if (!observation) return null;
  return {
    dataset_id: history.dataset_id,
    source_type: history.source_type,
    split: history.split,
    unit_id: history.unit_id,
    sensor: history.sensor,
    start_cycle: history.start_cycle,
    end_cycle: history.end_cycle,
    ...observation.source_evidence,
  };
}

function formatNumber(value) {
  return Number(value.toFixed(6)).toString();
}

export function evidencePromptIdentity(history, index) {
  const observation = history?.observations?.[index];
  if (!observation) return null;
  return [
    history.dataset_id,
    history.source_type,
    history.split,
    history.unit_id,
    history.sensor,
    history.start_cycle,
    history.end_cycle,
    observation.cycle,
    observation.source_evidence.source_sha256,
    observation.source_evidence.source_physical_line_1_based,
  ].join(":");
}

export function buildEvidencePrompt(history, index) {
  const evidence = evidenceFor(history, index);
  const identity = evidencePromptIdentity(history, index);
  if (!evidence || !identity || !Array.isArray(history.observations) || history.observations.length === 0) {
    throw new ContractError("A current validated History and selected observation are required");
  }
  const values = history.observations.map((observation) => observation.value);
  if (values.some((value) => typeof value !== "number" || !Number.isFinite(value))) {
    throw new ContractError("Evidence Prompt values must be finite non-null numbers");
  }
  const selected = history.observations[index];
  const count = values.length;
  const sum = values.reduce((total, value) => total + value, 0);
  const mean = sum / count;
  const first = values[0];
  const last = values[values.length - 1];
  const delta = last - first;
  const prompt = `FD001 EVIDENCE PROMPT
Use only the classified evidence below. Do not add external baselines, thresholds, diagnoses, health scores, failure causes, or RUL values.

[OBSERVED]
- Dataset ID: ${history.dataset_id}
- Source Type: ${history.source_type}
- Split: ${history.split}
- Unit ID: ${history.unit_id}
- Sensor ID: ${history.sensor}
- Cycle Range: ${history.start_cycle}-${history.end_cycle}
- API Observation Count: ${count}
- Selected Cycle: ${selected.cycle}
- Selected Sensor Value: ${formatNumber(selected.value)} (source-defined / unspecified physical unit)
- Source File: ${evidence.source_file}
- Source SHA-256: ${evidence.source_sha256}
- Source Physical Line (1-based): ${evidence.source_physical_line_1_based}
- Parsed Row Index (0-based): ${evidence.parsed_row_index_0_based}

[DERIVED]
- Calculation source: only the ${count} current API observations for ${history.split} Unit ${history.unit_id}, ${history.sensor}, cycles ${history.start_cycle}-${history.end_cycle}.
- Mean formula: Mean = sum(values) / N
- Mean calculation: ${formatNumber(sum)} / ${count} = ${formatNumber(mean)}
- Delta formula: Delta = last - first
- Delta calculation: ${formatNumber(last)} - ${formatNumber(first)} = ${formatNumber(delta)}
- These statistics are descriptive calculations, not an external baseline or a fault diagnosis.

[INFERRED]
- No verified fault, failure, anomaly, or failure cause is supported by this selected evidence alone.
- Any interpretation of the descriptive Mean or Delta must remain conditional and must not be presented as a verified fact.

[UNKNOWN]
- Physical engine condition: unknown; not observed in this simulated dataset.
- Failure cause: unknown; not provided by the API evidence.
- Health score: unknown; not provided by the API evidence.
- Warning or failure threshold: unknown; not provided by the API evidence.
- RUL prediction/value for this query: unknown; do not fabricate one.

[REQUIRED DISCLOSURES]
- NASA C-MAPSS FD001 is a simulated turbofan degradation dataset, not physical equipment field measurement.
- TRAIN contains simulated complete degradation trajectories.
- TEST contains truncated simulated trajectories; its last observed Cycle is not a failure time.
- TEST_RUL is an independent label at the last observed Cycle, not a Sensor Observation.
- Sensor trend and derived statistics are not a verified fault diagnosis.
- Do not insert an RUL value unless a validated API response explicitly provides it.

[REQUEST]
Summarize the evidence while preserving the OBSERVED, DERIVED, INFERRED, and UNKNOWN boundaries. Cite the selected source basename, SHA-256, physical line, and parsed row. State all limitations explicitly.`;

  return {
    identity,
    text: prompt,
    statistics: { count, sum, mean, first, last, delta },
  };
}

export async function copyPromptToClipboard(promptState, displayedText, activeIdentity, clipboard) {
  if (!promptState || promptState.identity !== activeIdentity || promptState.text !== displayedText) {
    throw new ContractError("The displayed Evidence Prompt is stale or invalid");
  }
  if (!clipboard || typeof clipboard.writeText !== "function") {
    throw new ContractError("Clipboard API is unavailable");
  }
  await clipboard.writeText(promptState.text);
  return promptState.text;
}

export function errorLabel(status) {
  if (status === 400) return "Query Validation Error";
  if (status === 404) return "Observation Not Found";
  if (status === 503) return "Source Not Validated";
  return "Connection Error";
}

export class RequestGate {
  #identity = 0;
  #controller = null;

  begin() {
    this.#controller?.abort();
    this.#controller = new AbortController();
    this.#identity += 1;
    return { identity: this.#identity, signal: this.#controller.signal };
  }

  isCurrent(identity) {
    return identity === this.#identity;
  }

  cancel() {
    this.#controller?.abort();
    this.#identity += 1;
  }
}
