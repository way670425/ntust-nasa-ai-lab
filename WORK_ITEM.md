# WORK_ITEM.md

## Active Work Item

TYPE: BOUNDED_WORK_ORDER
WORK_ITEM_ID: WO-M0-001
FROM: STUDENT-MAIN Brain
TO: MAIN Own Worker (Codex)
AUTHORIZED_BY: STUDENT
STATUS: COMMAND_DISPATCHED
MILESTONE: M0

## Objective

初始化 AI Team Governance
並同步到 GitHub 公開儲存庫。

## Authorized Deliverables

- AGENTS.md
- ROADMAP.md
- WORK_ITEM.md
- DECISIONS.md
- Initial Git Commit
- GitHub Repository
- Execution Report

## Authorized Repository

Repository Name:
ntust-nasa-ai-lab

Visibility:
PUBLIC

Default Branch:
main

## Acceptance Criteria

- 四個 Markdown 檔案完整建立
- Git Repository 正常初始化
- 首次 Commit 成功
- GitHub 公開儲存庫建立成功
- main 分支推送成功
- 本地 Commit SHA 與遠端一致
- 提供遠端 GitHub 連結

## STOP_IF

- 專案根目錄不明
- 目標檔案已存在且有衝突
- Git Repository 存在不相容歷史
- GitHub 認證失敗
- 遠端儲存庫名稱發生衝突
- 發現敏感檔案可能公開
- 無法安全完成推送

## Current Gate

M0: PENDING_VERIFICATION

不得由 Worker 自行改成 APPROVED。

## Next Role

STUDENT-MAIN Brain

## Scope Restriction

本工作單不授權 M1–M5 的實作或派工。
