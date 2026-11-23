# FD001 API / Raw Source Comparison

- Work item: `WO-M4-WEB-EVIDENCE-001`
- Date: 2026-11-23 (Asia/Taipei)
- Query: `/api/history?split=train&unit=1&sensor=7&start=1&end=20`
- Raw source basename: `train_FD001.txt`
- Raw source SHA-256: `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`
- Comparison command: `PYTHONDONTWRITEBYTECODE=1 python3 web/frontend/tests/verify_api_source.py`
- Exit code: `0`
- Result: **20/20 PASS; differences: NONE**

## Counts and mappings

| Check | Result |
|---|---|
| API observation count | 20 |
| Browser Table observation count | 20 |
| Chart observation count | 20 |
| Cycles compared | 20/20 equal |
| Sensor 7 values compared | 20/20 equal |
| `source_file` | 20/20 `train_FD001.txt` |
| `source_sha256` | 20/20 equal to accepted TRAIN hash |
| `source_physical_line_1_based` | 20/20 equal |
| `parsed_row_index_0_based` | 20/20 equal |
| Evidence Prompt source | Current API selection; Cycle/source/hash/line/index matched selected observation |
| Differences | NONE |

## Independent method

`verify_api_source.py` reads the accepted raw TXT in read-only mode, verifies the complete-file SHA-256, requires exactly 26 whitespace-delimited fields per source row, selects Unit 1 cycles 1–20, and extracts Sensor 7 from source column 12 (zero-based field index 11). It independently requests the live API and compares every cycle, numeric value, safe basename, hash, one-based physical line and zero-based parsed index.

The browser Chart and Table both consume the single validated `history.observations` array; the visible browser counted 20 rows and a 20-observation Chart. The source-comparison output records only counts and the accepted hash, not the bulk raw rows or a reconstructable export.
