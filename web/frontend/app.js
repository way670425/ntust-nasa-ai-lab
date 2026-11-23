import {
  ContractError,
  RequestGate,
  buildEvidencePrompt,
  copyPromptToClipboard,
  errorLabel,
  evidenceFor,
  evidencePromptIdentity,
  mapHistory,
  parseCatalog,
  parseHealth,
  parseHistory,
  parseUnits,
  refreshForSensor,
  resetForSplit,
  resetForUnit,
  validateCycleRange,
} from "./state.mjs?v=m4.1";

class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
  }
}

const elements = {
  validationBadge: document.querySelector("#validation-badge"),
  split: document.querySelector("#split-select"),
  unit: document.querySelector("#unit-select"),
  sensor: document.querySelector("#sensor-select"),
  start: document.querySelector("#start-cycle"),
  end: document.querySelector("#end-cycle"),
  query: document.querySelector("#query-button"),
  availableRange: document.querySelector("#available-range"),
  observationTotal: document.querySelector("#observation-total"),
  validationMessage: document.querySelector("#validation-message"),
  statusPanel: document.querySelector("#status-panel"),
  statusTitle: document.querySelector("#status-title"),
  statusDetail: document.querySelector("#status-detail"),
  chartTitle: document.querySelector("#chart-title"),
  chart: document.querySelector("#trend-chart"),
  chartEmpty: document.querySelector("#chart-empty"),
  pointCount: document.querySelector("#point-count"),
  tableBody: document.querySelector("#observation-body"),
  selectedCycle: document.querySelector("#selected-cycle"),
  generatePrompt: document.querySelector("#generate-prompt"),
  copyPrompt: document.querySelector("#copy-prompt"),
  promptOutput: document.querySelector("#prompt-output"),
  copyFeedback: document.querySelector("#copy-feedback"),
};

let state = {
  catalog: null,
  split: null,
  units: [],
  unit: null,
  sensor: null,
  start: null,
  end: null,
  history: null,
  selectedIndex: null,
  prompt: null,
};

const unitGate = new RequestGate();
const historyGate = new RequestGate();
let chartHitTargets = [];

async function fetchJson(path, signal) {
  let response;
  try {
    response = await fetch(path, { signal, headers: { Accept: "application/json" } });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError(0, "The local API connection could not be reached.");
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(response.status, "The API returned an unreadable response.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, payload?.error?.message || "The API rejected the request.");
  }
  return payload;
}

function setStatus(kind, title, detail) {
  elements.statusPanel.className = `status-panel ${kind}`;
  elements.statusTitle.textContent = title;
  elements.statusDetail.textContent = detail;
}

function setControlsEnabled(enabled) {
  for (const element of [elements.split, elements.unit, elements.sensor, elements.start, elements.end]) {
    element.disabled = !enabled;
  }
  elements.query.disabled = !enabled;
}

function setOptions(select, values, selectedValue, formatter = (value) => value) {
  select.replaceChildren();
  for (const value of values) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = formatter(value);
    option.selected = String(value) === String(selectedValue);
    select.append(option);
  }
}

function clearData(message = "No observations loaded") {
  invalidatePrompt("Prompt unavailable while data is loading, empty, or invalid.");
  state.history = null;
  state.selectedIndex = null;
  elements.pointCount.textContent = "0 observations";
  elements.chartTitle.textContent = "Select data to display a Sensor trend.";
  elements.chartEmpty.textContent = message;
  elements.chartEmpty.hidden = false;
  elements.tableBody.innerHTML = `<tr class="placeholder-row"><td colspan="6">${message}</td></tr>`;
  clearEvidence();
  drawChart();
}

function invalidatePrompt(message) {
  state.prompt = null;
  elements.promptOutput.textContent = "No valid prompt. Load a successful query and select an observation.";
  elements.generatePrompt.disabled = true;
  elements.copyPrompt.disabled = true;
  elements.copyFeedback.className = "copy-feedback";
  elements.copyFeedback.textContent = message;
}

function updatePrompt() {
  try {
    state.prompt = buildEvidencePrompt(state.history, state.selectedIndex);
    elements.promptOutput.textContent = state.prompt.text;
    elements.generatePrompt.disabled = false;
    elements.copyPrompt.disabled = false;
    elements.copyFeedback.className = "copy-feedback";
    elements.copyFeedback.textContent = "Prompt is current and ready to copy locally.";
  } catch (error) {
    invalidatePrompt(error.message || "Evidence Prompt is unavailable.");
  }
}

function clearEvidence() {
  document.querySelectorAll("[data-evidence]").forEach((node) => { node.textContent = "N/A"; });
  elements.selectedCycle.textContent = "No point";
}

function currentQuery() {
  return {
    split: state.split,
    unit: state.unit.unit_id,
    sensor: state.sensor,
    start: state.start,
    end: state.end,
  };
}

function querySignature(query) {
  return [query.split, query.unit, query.sensor, query.start, query.end].join(":");
}

function syncCycleInputs() {
  if (!state.unit) {
    elements.start.value = "";
    elements.end.value = "";
    elements.availableRange.textContent = "N/A";
    elements.observationTotal.textContent = "No Unit selected";
    return;
  }
  elements.start.min = state.unit.min_cycle;
  elements.start.max = state.unit.max_cycle;
  elements.end.min = state.unit.min_cycle;
  elements.end.max = state.unit.max_cycle;
  elements.start.value = state.start;
  elements.end.value = state.end;
  elements.availableRange.textContent = `${state.unit.min_cycle}–${state.unit.max_cycle}`;
  elements.observationTotal.textContent = `${state.unit.observation_count} source observations`;
}

function validateInputs() {
  const result = validateCycleRange(elements.start.value, elements.end.value, state.unit);
  elements.validationMessage.hidden = result.valid;
  elements.validationMessage.textContent = result.valid ? "" : result.message;
  return result;
}

async function loadUnits() {
  historyGate.cancel();
  clearData("Loading Units for the selected Split…");
  elements.unit.disabled = true;
  elements.start.disabled = true;
  elements.end.disabled = true;
  elements.query.disabled = true;
  setStatus("loading", "Loading", `Loading ${state.split} Engine Units from the validated API.`);
  const request = unitGate.begin();
  const requestedSplit = state.split;
  try {
    const payload = await fetchJson(`/api/units?split=${requestedSplit.toLowerCase()}`, request.signal);
    if (!unitGate.isCurrent(request.identity) || state.split !== requestedSplit) return;
    const units = parseUnits(payload, requestedSplit);
    state.units = units;
    state = resetForUnit(state, units[0]);
    setOptions(elements.unit, units.map((unit) => unit.unit_id), state.unit.unit_id, (value) => `Unit ${value}`);
    syncCycleInputs();
    elements.unit.disabled = false;
    elements.start.disabled = false;
    elements.end.disabled = false;
    elements.query.disabled = false;
    await loadHistory();
  } catch (error) {
    if (error.name === "AbortError") return;
    showError(error);
  }
}

async function loadHistory() {
  const validation = validateInputs();
  if (!validation.valid) return;
  state.start = validation.start;
  state.end = validation.end;
  clearData("Loading observations for the active query…");
  setStatus("loading", "Loading", "Requesting Sensor observations and source evidence.");
  const query = currentQuery();
  const signature = querySignature(query);
  const request = historyGate.begin();
  elements.query.disabled = true;
  const sensorNumber = query.sensor.replace("sensor_", "");
  const path = `/api/history?split=${query.split.toLowerCase()}&unit=${query.unit}&sensor=${sensorNumber}&start=${query.start}&end=${query.end}`;
  try {
    const payload = await fetchJson(path, request.signal);
    if (!historyGate.isCurrent(request.identity) || signature !== querySignature(currentQuery())) return;
    state.history = parseHistory(payload, query);
    state.selectedIndex = 0;
    renderHistory();
    setStatus("success", "Success", `${state.history.observation_count} validated observations loaded from ${state.history.split} Unit ${state.history.unit_id}.`);
  } catch (error) {
    if (error.name === "AbortError") return;
    showError(error);
  } finally {
    if (historyGate.isCurrent(request.identity)) elements.query.disabled = false;
  }
}

function showError(error) {
  const status = error instanceof ApiError ? error.status : 0;
  const title = error instanceof ContractError ? "Source Not Validated" : errorLabel(status);
  const detail = error.message || "The request could not be completed safely.";
  clearData(title);
  setStatus("error", title, detail);
  elements.query.disabled = !state.unit;
}

function renderHistory() {
  const { rows } = mapHistory(state.history);
  elements.chartEmpty.hidden = true;
  elements.pointCount.textContent = `${rows.length} observations`;
  elements.chartTitle.textContent = `${state.history.split} · Unit ${state.history.unit_id} · ${state.history.sensor} · Cycles ${state.history.start_cycle}–${state.history.end_cycle}`;
  elements.tableBody.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.dataset.index = row.index;
    tr.tabIndex = 0;
    tr.innerHTML = `
      <td>${row.cycle}</td>
      <td>${row.sensor}</td>
      <td>${row.value}</td>
      <td>${row.source_evidence.source_file}</td>
      <td>${row.source_evidence.source_physical_line_1_based}</td>
      <td>${row.source_evidence.parsed_row_index_0_based}</td>`;
    tr.addEventListener("click", () => selectObservation(row.index));
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectObservation(row.index);
      }
    });
    elements.tableBody.append(tr);
  }
  selectObservation(state.selectedIndex, false);
}

function selectObservation(index, focusRow = true) {
  if (!state.history?.observations?.[index]) return;
  state.selectedIndex = index;
  elements.tableBody.querySelectorAll("tr[data-index]").forEach((row) => {
    row.classList.toggle("selected", Number(row.dataset.index) === index);
  });
  const observation = state.history.observations[index];
  elements.selectedCycle.textContent = `Cycle ${observation.cycle}`;
  const evidence = evidenceFor(state.history, index);
  const values = { ...evidence };
  document.querySelectorAll("[data-evidence]").forEach((node) => {
    const value = values[node.dataset.evidence];
    node.textContent = value === null || value === undefined ? "N/A" : String(value);
  });
  updatePrompt();
  drawChart();
  if (focusRow) {
    elements.tableBody.querySelector(`tr[data-index="${index}"]`)?.scrollIntoView({ block: "nearest" });
  }
}

function drawChart() {
  const canvas = elements.chart;
  const bounds = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(bounds.width, 320);
  const height = Math.max(bounds.height, 300);
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);
  context.clearRect(0, 0, width, height);
  chartHitTargets = [];
  if (!state.history) return;

  const points = mapHistory(state.history).points;
  const padding = { top: 28, right: 24, bottom: 42, left: 70 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const cycles = points.map((point) => point.cycle);
  const values = points.map((point) => point.value);
  const minCycle = Math.min(...cycles);
  const maxCycle = Math.max(...cycles);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const valuePad = rawMin === rawMax ? Math.max(Math.abs(rawMin) * .01, 1) : (rawMax - rawMin) * .12;
  const minValue = rawMin - valuePad;
  const maxValue = rawMax + valuePad;
  const x = (cycle) => padding.left + ((cycle - minCycle) / Math.max(maxCycle - minCycle, 1)) * innerWidth;
  const y = (value) => padding.top + (1 - (value - minValue) / (maxValue - minValue)) * innerHeight;

  context.font = "12px system-ui";
  context.strokeStyle = "#243a55";
  context.fillStyle = "#9cb0c7";
  context.lineWidth = 1;
  for (let tick = 0; tick <= 4; tick += 1) {
    const yPosition = padding.top + (tick / 4) * innerHeight;
    const labelValue = maxValue - (tick / 4) * (maxValue - minValue);
    context.beginPath();
    context.moveTo(padding.left, yPosition);
    context.lineTo(width - padding.right, yPosition);
    context.stroke();
    context.textAlign = "right";
    context.fillText(labelValue.toFixed(Math.abs(labelValue) >= 100 ? 2 : 4), padding.left - 10, yPosition + 4);
  }
  const xTicks = Math.min(5, points.length - 1);
  for (let tick = 0; tick <= xTicks; tick += 1) {
    const cycle = Math.round(minCycle + (tick / Math.max(xTicks, 1)) * (maxCycle - minCycle));
    context.textAlign = "center";
    context.fillText(String(cycle), x(cycle), height - 16);
  }

  context.strokeStyle = "#4ed8d3";
  context.lineWidth = 2;
  context.beginPath();
  points.forEach((point, index) => {
    const px = x(point.cycle);
    const py = y(point.value);
    if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
    chartHitTargets.push({ x: px, y: py, index: point.index });
  });
  context.stroke();

  for (const target of chartHitTargets) {
    const selected = target.index === state.selectedIndex;
    context.beginPath();
    context.arc(target.x, target.y, selected ? 6 : 3.3, 0, Math.PI * 2);
    context.fillStyle = selected ? "#ff9d6c" : "#4ed8d3";
    context.fill();
    if (selected) {
      context.strokeStyle = "#f0f6fc";
      context.lineWidth = 2;
      context.stroke();
    }
  }
}

elements.chart.addEventListener("click", (event) => {
  if (!chartHitTargets.length) return;
  const bounds = elements.chart.getBoundingClientRect();
  const pointer = { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  const nearest = chartHitTargets.reduce((best, target) => {
    const distance = Math.hypot(target.x - pointer.x, target.y - pointer.y);
    return distance < best.distance ? { target, distance } : best;
  }, { target: null, distance: Number.POSITIVE_INFINITY });
  if (nearest.target && nearest.distance <= 18) selectObservation(nearest.target.index);
});

elements.split.addEventListener("change", () => {
  state = resetForSplit(state, elements.split.value);
  syncCycleInputs();
  loadUnits();
});

elements.unit.addEventListener("change", () => {
  const unit = state.units.find((candidate) => candidate.unit_id === Number(elements.unit.value));
  if (!unit) return;
  state = resetForUnit(state, unit);
  syncCycleInputs();
  loadHistory();
});

elements.sensor.addEventListener("change", () => {
  state = refreshForSensor(state, elements.sensor.value);
  loadHistory();
});

elements.query.addEventListener("click", loadHistory);
elements.start.addEventListener("change", loadHistory);
elements.end.addEventListener("change", loadHistory);
elements.generatePrompt.addEventListener("click", updatePrompt);
elements.copyPrompt.addEventListener("click", async () => {
  elements.copyFeedback.className = "copy-feedback";
  elements.copyFeedback.textContent = "Copying the current prompt…";
  try {
    const activeIdentity = evidencePromptIdentity(state.history, state.selectedIndex);
    await copyPromptToClipboard(
      state.prompt,
      elements.promptOutput.textContent,
      activeIdentity,
      navigator.clipboard,
    );
    elements.copyFeedback.className = "copy-feedback success";
    elements.copyFeedback.textContent = "Copied current Evidence Prompt to clipboard.";
  } catch (error) {
    elements.copyFeedback.className = "copy-feedback error";
    elements.copyFeedback.textContent = `Copy failed: ${error.message || "Clipboard write was rejected."}`;
  }
});
window.addEventListener("resize", drawChart);

async function bootstrap() {
  setControlsEnabled(false);
  clearData();
  setStatus("loading", "Loading", "Validating the source and loading the API Catalog.");
  try {
    const [healthPayload, catalogPayload] = await Promise.all([
      fetchJson("/api/health"),
      fetchJson("/api/catalog"),
    ]);
    parseHealth(healthPayload);
    const catalog = parseCatalog(catalogPayload);
    state.catalog = catalog;
    state.split = catalog.available_splits[0];
    state.sensor = catalog.sensor_names[6] || catalog.sensor_names[0];
    setOptions(elements.split, catalog.available_splits, state.split);
    setOptions(elements.sensor, catalog.sensor_names, state.sensor);
    elements.validationBadge.textContent = "Source Validated";
    elements.validationBadge.classList.add("valid");
    setControlsEnabled(true);
    await loadUnits();
  } catch (error) {
    showError(error);
    elements.validationBadge.textContent = errorLabel(error.status || 0);
    setControlsEnabled(false);
  }
}

bootstrap();
