# DECISIONS.md

## DEC-0001: Governance Authority

Decision:
STUDENT 為最終核准者。
STUDENT-MAIN 負責治理與驗收。
Worker 負責有界執行。

Status:
APPROVED_BY_STUDENT

## DEC-0002: Milestone Governance

Decision:
專案分成 M0–M5。
所有階段需經 Gate 驗收。
不得自動進入下一階段。

Status:
APPROVED_BY_STUDENT

## DEC-0003: M1 Synthetic Data Policy

Decision:
M1 使用六筆 synthetic_sensor.csv
作為本地派工訓練資料。

不得宣稱其為 NASA 真實數據。

Status:
APPROVED_AS_PLAN
DATA_NOT_YET_VERIFIED

## DEC-0004: NASA Data Integrity

Decision:
NASA FD001 原始資料預設唯讀。
必須保存來源與數值追溯能力。

Status:
APPROVED_AS_PLAN

## DEC-0005: GitHub Repository

Decision:
建立 GitHub 公開儲存庫。

Repository:
ntust-nasa-ai-lab

Default Branch:
main

Authorized Content:
M0 Governance Files Only

Status:
APPROVED_BY_STUDENT

## DEC-0006: Worker Authorization

Decision:
學生已批准 WO-M0-001 執行。

授權範圍僅包含 M0 治理文件、
Git 初始化、首次 Commit、
GitHub 儲存庫建立與同步。

Status:
COMMAND_DISPATCHED

## DEC-0007: Gate Control

Decision:
Worker 完成任務不代表 Gate PASS。
必須由 STUDENT-MAIN 驗收，
並由學生批准下一階段。

Status:
ACTIVE
