# ROADMAP.md

## M0 - AI Team Governance

Goal:
建立專案治理文件、任務協定與版本控制。

Input:
學生批准的 M0 治理規劃。

Deliverables:
AGENTS.md
ROADMAP.md
WORK_ITEM.md
DECISIONS.md
Git Commit
GitHub Repository

Responsible:
STUDENT-MAIN Brain
MAIN Own Worker (Codex)

Acceptance:
四個治理檔案建立完成。
Git Commit 成功。
GitHub 推送成功。
提供驗證證據。

STOP_IF:
治理檔案不完整。
Git 操作失敗。
GitHub 授權失敗。
檔案發生衝突。

Next:
STUDENT-MAIN Gate M0 Review。

## M1 - Synthetic CSV Dispatch Training

Goal:
使用本地六筆 synthetic_sensor.csv
驗證資料讀取、選擇、趨勢與 Evidence Prompt 流程。

Input:
synthetic_sensor.csv
M0 治理契約

Deliverables:
CSV Validator
Minimal Query Interface
Trend Demo
Synthetic Evidence Prompt
M1 Test Report

Responsible:
STUDENT-MAIN
Authorized Codex/Claude Worker

Acceptance:
確認六筆資料。
欄位符合契約。
數值與來源一致。
Prompt 標記 SYNTHETIC。

STOP_IF:
資料缺失。
欄位不符。
數值不一致。
來源標記錯誤。

Next:
STUDENT-MAIN Gate M1 Review。

## M2 - NASA FD001 Integration

Goal:
建立真實 FD001 資料載入與來源追溯機制。

Input:
NASA FD001 原始資料
M1 已驗收成果

Deliverables:
FD001 Parser
Schema Mapping
Source Provenance
Data Validation Report

Responsible:
FD001 Data Brain / Authorized Worker

Acceptance:
欄位正確。
資料筆數可核對。
Unit / Cycle / Sensor 可追溯。
原始資料保持不變。

STOP_IF:
來源不明。
欄位錯位。
資料缺失。
無法追溯原始資料。

Next:
STUDENT-MAIN Gate M2 Review。

## M3 - Health Analysis Website

Goal:
建立本地互動式引擎健康分析網站。

Input:
M2 已驗證 FD001 資料介面

Deliverables:
Local Website
Engine Unit Selector
Cycle Selector
Sensor Selector
Trend Chart
Source Evidence Panel

Responsible:
Web Application Brain / Authorized Worker

Acceptance:
網站可在本地執行。
選取功能正確。
圖表與來源數值一致。
資料可追溯。

STOP_IF:
網站無法啟動。
選取結果錯誤。
圖表使用虛構數據。
來源資訊缺失。

Next:
STUDENT-MAIN Gate M3 Review。

## M4 - Evidence Prompt Generator

Goal:
產生包含真實數值與來源的 Evidence Prompt。

Input:
M3 Website Selection State
M2 Validated Source Records

Deliverables:
Evidence Prompt Generator
Prompt Preview
Copy Function
Evidence Traceability

Responsible:
Evidence Prompt Brain / Authorized Worker

Acceptance:
Prompt 數值正確。
來源完整。
相同輸入可重現相同輸出。
不編造分析結論。

STOP_IF:
Prompt 數值不一致。
缺少來源。
產生未經證實的診斷或 RUL。

Next:
STUDENT-MAIN Gate M4 Review。

## M5 - Integration and Final Acceptance

Goal:
完成網站整合、測試與本地交付。

Input:
M0–M4 已驗收成果

Deliverables:
Final Website
README.md
Test Suite
Traceability Matrix
Final Acceptance Report

Responsible:
QA / Release Brain
STUDENT-MAIN

Acceptance:
本地可重現執行。
完整操作流程通過。
測試與資料來源一致。
學生完成最終簽核。

STOP_IF:
核心功能失敗。
資料證據不一致。
測試無法重現。
未取得最終核准。

Next:
STUDENT Final Acceptance。

## Milestone Rule

M0 → M1 → M2 → M3 → M4 → M5

所有 Milestone 必須經過：

Worker Executes
→ Worker Reports
→ STUDENT-MAIN Reviews
→ STUDENT Approves
→ Next Milestone

禁止自動跨階段派工。
