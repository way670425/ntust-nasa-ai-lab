# M5 R2 Evidence Prompt and Clipboard Validation

- Active query: TRAIN Unit 1, `sensor_7`, Cycles 1–20
- Selected observation: Cycle 1, value 554.36
- Result: **PASS**

## Verified content

- Dataset ID and Source Type matched the live API.
- Split, Unit, Sensor, range, selected Cycle and Sensor value matched the active Browser state.
- Source file, SHA-256, physical line 1 and parsed row 0 matched current API provenance.
- Source column mapping identified `sensor_7` as one-based column 12.
- `[OBSERVED]`, `[DERIVED]`, `[INFERRED]` and `[UNKNOWN]` were present.
- Mean reproduced as `11082.51 / 20 = 554.1255`.
- Delta reproduced as `554.81 - 554.36 = 0.45`.
- M2 metadata was labelled `Scope: SPLIT_LEVEL` and explicitly not selected-Unit statistics.
- TRAIN and TEST source/quality contexts remained isolated.
- External AI safety instructions prohibited transmission/fabrication and the Frontend made no external AI request.

## Clipboard

- Browser action: Click `Copy Prompt`.
- Visible Prompt characters: 5580.
- Browser Clipboard characters: 5580.
- Exact string equality: TRUE.
- Success was proven by reading Clipboard content, not by toast alone.

## Inference boundaries

- No fabricated Sensor unit.
- No confirmed/unsupported fault diagnosis.
- No numeric warning or failure threshold.
- No numeric health score.
- No fabricated RUL value.
- Health score and RUL remained explicitly UNKNOWN.

Evidence: `web/m5/browser_evidence/r2_evidence_prompt_copy.png`.
