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
  };
}

export function resetForUnit(state, unit) {
  const start = unit.min_cycle;
  const end = Math.min(unit.max_cycle, start + 19);
  return { ...state, unit, start, end, history: null, selectedIndex: null };
}

export function refreshForSensor(state, sensor) {
  return { ...state, sensor, history: null, selectedIndex: null };
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
