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
