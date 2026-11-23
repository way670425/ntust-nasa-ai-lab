# FD001 Read-Only API

This local-only API serves validated NASA C-MAPSS FD001 simulated engine-degradation observations. It does not represent physical engine field measurements, diagnose failures, or predict RUL.

## Start

Python 3.10 or newer is required; no third-party packages are used.

```sh
python3 web/run_server.py
```

The server binds to `127.0.0.1:8000` by default. A different trusted local data directory may be selected at startup with `--data-dir`; API callers cannot submit file paths.

## Endpoints

- `GET /api/health`
- `GET /api/catalog`
- `GET /api/units?split=train`
- `GET /api/units?split=test`
- `GET /api/history?split=train&unit=1&sensor=7&start=1&end=20`

All source files are validated against the accepted SHA-256 values and schema before any query succeeds. Evidence contains only a safe source basename, complete-file hash, one-based physical line, and zero-based parsed row index. `TEST_RUL` is an independent positional-label source and is never exposed as Sensor history.

Each endpoint rejects unknown or repeated query parameters with HTTP 400. `split` is required by `/api/units`; `split`, `unit`, `sensor`, `start`, and `end` are all required by `/api/history`. `/api/health` and `/api/catalog` accept no query parameters. Sensor selectors must be integer IDs from 1 through 21.

The Catalog `observation_schema` lists all 26 source columns in one-based source order. Every entry provides `name`, `data_type`, `nullable`, `source_column_position`, and `query_semantics`; Sensor and operating-setting physical units remain source-defined or unspecified.

## Test

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/tests -v
```

The test suite independently parses TRAIN Unit 1, cycles 1–20, and compares every Sensor 7 value and provenance coordinate with the API response. It also covers split isolation, invalid queries, missing/tampered/malformed sources, non-finite values, safe errors, and forbidden write methods.

## Frontend

Start the validated API and the same-origin frontend proxy in separate terminals:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 web/run_server.py
PYTHONDONTWRITEBYTECODE=1 python3 web/frontend_server.py
```

Open `http://127.0.0.1:8001/`. The proxy serves only the static frontend and forwards `/api/*` reads to the accepted M3-A service at `127.0.0.1:8000`; it does not modify the API contract or source data.

The interface dynamically loads Splits, Units, Sensors, cycle ranges, observations, and provenance from the API. The Canvas chart draws only returned observations with straight line segments—no interpolation, smoothing, or thresholds. Chart points and table rows share the same observation index and update the selected evidence together. AbortController and request identities prevent stale responses from overwriting a newer selection.

Frontend automated tests:

```sh
node --test web/frontend/tests/state.test.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s web/frontend/tests -p 'test_*.py' -v
```

`web/frontend/tests/uat_error_harness.py` is a TEST_ONLY Browser UAT fixture for verifying the required 400, 404, 503, and connection-failure UI labels. It is not a formal data source and is never used as source-integrity evidence.
