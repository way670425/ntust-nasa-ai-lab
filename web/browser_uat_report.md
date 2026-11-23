# FD001 Frontend Browser UAT Report

- Work item: `WO-M3-WEB-FRONTEND-001`
- Date: 2026-11-23 (Asia/Taipei)
- Browser: Google Chrome 157.0.8103.80
- Browser mode: visible Chrome controlled through real UI interactions
- Formal integration: accepted M3-A API on `127.0.0.1:8000` using validated local FD001 sources
- Frontend: same-origin proxy on `127.0.0.1:8001`
- Result: 12 PASS / 0 FAIL

An initial visual inspection found that the Chart loading overlay remained visible after a successful response because author CSS overrode the HTML `hidden` state. The CSS was corrected with an explicit hidden rule, the page was reloaded, and all cases below were run against the corrected frontend. The failed pre-fix observation is not counted as a PASS.

| ID | Operation | Expected | Actual | Result |
|---|---|---|---|---|
| UAT_01 | Open the local website | Website loads normally | Title, disclosure, selectors, validated badge, 20-row Chart/Table and Evidence loaded | PASS |
| UAT_02 | Switch TRAIN to TEST | Split and Unit list update | TEST Unit 1 range changed to 1–31; rows and Evidence used `test_FD001.txt` | PASS |
| UAT_03 | Select Engine Unit 2 | Unit and cycle range update | TEST Unit 2 range changed to 1–49; History and Evidence used Unit 2 | PASS |
| UAT_04 | Switch Sensor 7 to Sensor 1 | Chart and Table update together | All rows used `sensor_1`; constant value 518.67 produced a horizontal line | PASS |
| UAT_05 | Set Cycle range 5–10 | Query range updates correctly | Exactly 6 rows, cycles 5 through 10, were shown | PASS |
| UAT_06 | Inspect Trend Chart | Chart matches API observations | Six source observations were drawn in cycle order; no interpolation, smoothing, or thresholds | PASS |
| UAT_07 | Inspect Observation Table | Table matches API | Cycle, Sensor, value, basename, physical line and parsed row matched API values | PASS |
| UAT_08 | Select table row and chart point | Evidence stays consistent | Cycle 7 row mapped to line 38/row 37; chart Cycle 9 mapped to line 40/row 39 | PASS |
| UAT_09 | Exercise 400, 404 and 503 responses | Required error classifications display | TEST_ONLY harness displayed Query Validation Error, Observation Not Found and Source Not Validated; no stale evidence remained | PASS |
| UAT_10 | Point proxy at unavailable API | Connection Error displays | Frontend showed Connection Error with 0 rows and N/A evidence | PASS |
| UAT_11 | Review all website text | No invented fault or RUL conclusions | Required simulation disclosure present; forbidden phrase scan returned no matches | PASS |
| UAT_12 | Rapidly select TEST then TRAIN | Stale TEST data never overwrites TRAIN | Final Chart, Table and Evidence were exclusively TRAIN / `train_FD001.txt` | PASS |

## Public browser evidence

- `web/browser_evidence/browser_observations.md`

The evidence records only safe dataset identifiers, source basenames, accepted hashes/coordinates, and UI results. It contains no private absolute path, credential, secret, or raw source row collection.

## Boundary

The 400/404/503 error-display checks use a clearly identified TEST_ONLY harness because the validated production source must not be corrupted to force a 503. Formal API integration, trend values, Table values, Evidence, and row provenance were all verified against the real accepted API and local trusted sources.

This Worker UAT result is candidate evidence for Web Brain review. It is not an M3-B Gate decision and does not authorize M4.
