# M5 R2 Real API Interruption and Recovery

- Result: **PASS**
- Frontend process remained the owned PID 59562 throughout the interruption.

## Sequence

1. Confirmed API PID 59558 belonged to `web/run_server.py` and Health returned HTTP 200.
2. Sent SIGTERM only to PID 59558; API became unreachable.
3. Confirmed Frontend remained HTTP 200.
4. Repeated the valid Browser query.
5. Observed `Connection Error`, 0 Chart observations, 0 Table rows, cleared Evidence, invalid Prompt and disabled Copy.
6. Started `PYTHONDONTWRITEBYTECODE=1 python3 web/run_server.py` as PID 60051.
7. Confirmed recovered Health HTTP 200 with `data_validated=true` and `read_only=true`.
8. Repeated TRAIN Unit 1 `sensor_7` Cycles 1–20.
9. Observed Success, 20 rows, `train_FD001.txt` Evidence, rebuilt Prompt and enabled Copy.
10. Re-ran independent source comparison after recovery: 20/20 match, differences NONE.

The original API termination is recorded as stopped by SIGTERM, not as a fabricated exit code 0. The recovered API and Frontend remained running only until final evidence completion and were then stopped through the owned PID shutdown script.

Evidence: `r2_api_disconnected.png` and `r2_api_recovered.png`.
