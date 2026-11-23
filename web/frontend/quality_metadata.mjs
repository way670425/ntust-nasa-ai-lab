export const M2_QUALITY_METADATA = Object.freeze({
  metadata_version: "WO-M2-RESEARCH-001-B/v1",
  dataset_id: "NASA_CMAPSS_FD001",
  source_type: "NASA_FD001_LOCAL_TRUSTED",
  report_source: "research/m2/data_quality_report.md",
  contract_source: "research/m2/data_contract.md",
  work_item_id: "WO-M2-RESEARCH-001-B",
  scope: "SPLIT_LEVEL",
  near_constant_method: "non-constant and (max-min)/max(abs(min),abs(max),1) <= 1e-4",
  test_rul: Object.freeze({
    source_file: "RUL_FD001.txt",
    source_sha256: "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
    semantics: "Independent positional rul_at_last_observed_cycle label; not a per-Cycle Sensor Observation.",
  }),
  splits: Object.freeze({
    TRAIN: Object.freeze({
      source_file: "train_FD001.txt",
      source_sha256: "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
      observations: 20631,
      units: 100,
      missing_values: 0,
      non_finite_values: 0,
      duplicate_unit_cycle: 0,
      invalid_cycle: 0,
      missing_cycles: 0,
      parsing_anomalies: 0,
      constant_sensors: Object.freeze([1, 5, 10, 16, 18, 19]),
      near_constant_sensors: Object.freeze([]),
    }),
    TEST: Object.freeze({
      source_file: "test_FD001.txt",
      source_sha256: "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
      observations: 13096,
      units: 100,
      missing_values: 0,
      non_finite_values: 0,
      duplicate_unit_cycle: 0,
      invalid_cycle: 0,
      missing_cycles: 0,
      parsing_anomalies: 0,
      constant_sensors: Object.freeze([1, 5, 10, 16, 18, 19]),
      near_constant_sensors: Object.freeze([]),
    }),
  }),
});

export function selectedSensorSourceColumn(sensorName) {
  const match = /^sensor_([1-9]|1[0-9]|2[01])$/.exec(sensorName || "");
  return match ? Number(match[1]) + 5 : null;
}
