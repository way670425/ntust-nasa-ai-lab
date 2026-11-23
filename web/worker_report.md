# Web Own Worker M4 Execution Report

- Type: `WORKER_TO_BRAIN_RETURN`
- Work item: `WO-M4-WEB-EVIDENCE-001`
- From: Web Own Worker
- To: STUDENT-WEB Brain
- Execution date: 2026-11-23 (Asia/Taipei)
- Worker execution: `SUCCESS` (candidate delivery; Brain verification required)
- GitHub AGENTS read: `TRUE`
- Base commit: `91567f2649c382cb3f4d8c7fbc2669171d7c4d82`
- Result commit: the Git commit containing this report; full SHA is reported in the external Worker return after push
- Worker Gate declaration: `PROHIBITED`

## Delivered implementation

- Added a local Evidence Prompt panel with automatic refresh, explicit Refresh action, readable output, Copy Prompt and visible success/failure feedback.
- Prompt identity binds dataset, source type, Split, Unit, Sensor, query range, selected Cycle, source hash and physical line. Loading/error/empty/selection changes invalidate the previous Prompt.
- OBSERVED contains current API identity/value/provenance. DERIVED contains reproducible Mean and Delta formulas over the current API observations. INFERRED remains conditional. UNKNOWN identifies unsupported condition, cause, score, threshold and RUL.
- Required TRAIN/TEST/TEST_RUL simulation disclosures are included. No Prompt is sent to an external service.
- Copy rejects stale, altered, unavailable and failed writes; successful browser copy was verified byte-for-byte against the visible current Prompt.
- Added versioned ES-module URLs so a browser cannot combine new HTML with cached pre-M4 JavaScript.

No M3-A API/Loader, Research file, data file, governance file or raw FD001 source was modified.

## Verification summary

| Check | Worker result |
|---|---|
| M3-A API regression | 14/14 PASS |
| Frontend state and Evidence Prompt tests | 16/16 PASS |
| Frontend server tests | 4/4 PASS |
| Automated total | 34/34 PASS |
| Real API / raw source comparison | 20/20 PASS; NONE different |
| Browser UAT | 16/16 PASS |
| Clipboard equality | PASS; 2,760/2,760 characters exact |
| Safe screenshots | 4 visually reviewed artifacts |
| Forbidden diagnosis/threshold/RUL scan | PASS |
| Source hashes | TRAIN / TEST / TEST_RUL all matched |

## Automated commands

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/tests -v
# Exit 0: 14 passed

node --test web/frontend/tests/state.test.mjs web/frontend/tests/evidence_prompt.test.mjs
# Exit 0: 16 passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/frontend/tests -p 'test_*.py' -v
# Exit 0: 4 passed

PYTHONDONTWRITEBYTECODE=1 python3 web/frontend/tests/verify_api_source.py
# Exit 0: 20/20 matched; differences NONE
```

Coverage includes Prompt mapping/classification/formulas/disclosures, source provenance, selection and Split isolation, stale Prompt prevention, exact copy, Clipboard failure, invalid/null/non-finite data, forbidden claim patterns, existing API contract/source validation, same-origin proxy and safe error handling.

## Browser evidence

- Browser: Google Chrome 157.0.8103.80, macOS 27.0.1 arm64
- UAT: `web/browser_uat_report.md`
- Observations and images: `web/browser_evidence/browser_observations.md`
- API/source report: `web/api_source_comparison.md`

Four real-browser images cover the initial TRAIN query, 20-point Chart with selected Cycle 20 Evidence, Cycle 10 Prompt and copy feedback, and switched TEST Unit 2 sensor_8 state. They contain no private path, secret or bulk raw rows.

## Failure/correction evidence

- Corrected one faulty copy-test expectation before the clean full run.
- Added module cache-version parameters after the first browser load exposed stale JavaScript.
- Did not accept the CUA clipboard bridge as proof; repeated exact-copy verification through macOS Clipboard and a browser context with explicit Clipboard permissions.
- Did not count a missed approximate Canvas click; repeated using the application's coordinate formula and verified Cycle 20 provenance.

## Changed files

- `web/README.md`
- `web/frontend/index.html`
- `web/frontend/app.js`
- `web/frontend/state.mjs`
- `web/frontend/styles.css`
- `web/frontend/tests/evidence_prompt.test.mjs`
- `web/frontend/tests/verify_api_source.py`
- `web/browser_uat_report.md`
- `web/browser_evidence/browser_observations.md`
- `web/browser_evidence/m4_initial.png`
- `web/browser_evidence/m4_chart_selected_evidence.png`
- `web/browser_evidence/m4_evidence_prompt.png`
- `web/browser_evidence/m4_switched_selection.png`
- `web/api_source_comparison.md`
- `web/worker_report.md`

## Boundary

- `STOP_IF_TRIGGERED: NONE`
- Existing untracked local Research/data artifacts were preserved and excluded from staging.
- This report does not declare M4 Gate PASS and does not authorize or begin M5.
- `RETURN_TO: STUDENT-WEB Brain`
