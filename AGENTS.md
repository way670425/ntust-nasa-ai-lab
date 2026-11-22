# AGENTS.md

## Project

NTUST NASA AI Lab

## Project Goal

建立 NASA C-MAPSS FD001 引擎健康分析網站。

最終網站必須支援：

- Engine Unit 選擇
- Cycle 選擇
- Sensor 選擇
- 真實感測器數據展示
- Sensor Trend Visualization
- Source Evidence Traceability
- Evidence Prompt Generation

## Authority Hierarchy

LEVEL 1: STUDENT（老闆）
- 專案最終決策者
- 核准各階段工作
- 核准工作範圍變更
- 核准進入下一 Milestone

LEVEL 2: STUDENT-MAIN Brain（總經理）
- 專案治理
- Roadmap 管理
- 工作單規劃
- 任務邊界管理
- Worker 成果驗收
- STOP_IF 判定
- 向學生回報

LEVEL 3: MAIN Own Worker (Codex)
- 依正式工作單執行
- 建立或修改授權範圍內的檔案
- 執行必要測試
- 提交執行證據
- 回報失敗與阻礙
- 不得自行新增 Milestone

## Read-Only Boundary

以下資料預設為唯讀：

- synthetic_sensor.csv
- NASA C-MAPSS FD001 原始資料
- train_FD001.txt
- test_FD001.txt
- RUL_FD001.txt
- 其他未明確授權修改的既有資料與程式碼

不得修改、刪除、覆寫上述檔案。

目前 M0 不得解析或處理這些資料。

## Write Boundary

WO-M0-001 僅允許：

- AGENTS.md
- ROADMAP.md
- WORK_ITEM.md
- DECISIONS.md
- Git 初始化及必要版本控制設定
- GitHub 公開儲存庫建立與授權內容推送

不得修改其他專案檔案。

## Execution Governance

所有 Worker 任務必須具有：

- TYPE
- WORK_ITEM_ID
- OBJECTIVE
- INPUT
- DELIVERABLES
- ACCEPTANCE
- STOP_IF
- REPORT

Worker 不得將自行測試 PASS 視為正式 Gate PASS。

只有 STUDENT-MAIN 可以提出 Gate 驗收結論。
學生保留下一階段最終核准權。

## Data Integrity

SYNTHETIC 與 NASA_FD001 必須明確區分。

不得：

- 將合成數據標示為 NASA 真實資料
- 編造 Sensor 數值
- 編造資料來源
- 捏造 RUL 預測
- 聲稱讀取尚未讀取的本地檔案

## STOP Policy

發生下列情況必須停止：

- 權限不足
- 工作範圍不明
- 檔案衝突
- 資料來源不明
- Git 操作可能破壞既有歷史
- GitHub 身分未授權
- 發現敏感資料可能被公開
- 任務要求超出本工作單

停止後必須回報 STUDENT-MAIN。

## Single Main Sequential Development

1. 專案採單一 main 分支、循序開發。
   同一時間只允許一個 Worker 執行。

2. 所有 Brain 派工前，必須讀取
   GitHub main 最新 AGENTS.md。

3. 所有 Worker 開發前，必須同步
   最新 main 並遵守工作單授權範圍。

4. Worker 完成後，必須執行測試、
   Commit 並 Push 成果至 GitHub main。

5. 所屬 Brain 必須從 GitHub 實際讀取
   Commit、檔案及測試證據，
   確認正確後才能回報 PASS。

6. 前一項工作尚未經 Brain Review
   與 MAIN 授權，下一個 Worker 不得開始。

7. MAIN Own Worker 負責維護本地整合環境，
   確保本地專案資料夾保有已核准的
   Research 與 Web 成果供網站測試。

8. NASA FD001 原始資料保持本地唯讀，
   不得上傳 GitHub。

9. 發現錯誤時，必須建立新的修正 Commit，
   禁止 Force Push 或覆寫 Git 歷史。

10. GitHub 無法存取、Push 失敗或
    Brain 無法驗證成果時，
    必須回報 BLOCKED。
