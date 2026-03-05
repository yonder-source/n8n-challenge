# Decision Log

> 用來記錄影響實作、維護或架構的決策。新條目加在最上方。

## Template
### [YYYY-MM-DD] 決策標題
- 背景：
- 決策：
- 原因：
- 影響：
- 替代方案：
- 狀態：Proposed | Accepted | Deprecated

---

## Entries

### [2026-03-05] 建立專案長期記憶機制
- 背景：多輪開發時，對話上下文不會永久保留，容易重複前情提要。
- 決策：建立 `docs/project-memory.md` 與 `docs/decision-log.md`，並在 `AGENTS.md` 規範每次任務前先讀取。
- 原因：降低溝通成本，保留可追溯的決策脈絡。
- 影響：每次交付後需額外維護少量文件。
- 替代方案：僅依賴對話紀錄（不採用，跨 session 易遺失脈絡）。
- 狀態：Accepted
