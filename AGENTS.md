# AGENTS

## Session Memory Rules
1. 每次開始處理任務前，先讀取 `docs/project-memory.md` 與 `docs/decision-log.md`。
2. 回覆與實作時，需優先遵循上述兩份文件中的既有決策與脈絡。
3. 每次完成一段可交付工作後，更新 `docs/project-memory.md`（狀態與下一步）與 `docs/decision-log.md`（若有新決策）。
4. 若兩份文件內容衝突，以 `docs/decision-log.md` 的最新決策為準，並同步修正 `docs/project-memory.md`。
