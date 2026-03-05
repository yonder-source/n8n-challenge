# Project Memory

## 目前目標
- 交付可匯入 n8n 的競賽級 Email Classifier 工作流，並保留可產品化的安全與擴充設計。
- 在不造成標籤洩漏前提下，完成可評測的資料準備、檢索與信心決策鏈路。

## 已完成
- 專案骨架與核心目錄已建立：`workflows/`、`src/config/`、`src/mappings/`、`src/prompts/`、`data/`、`eval/`、`docs/`、`scripts/`。
- 已實作並執行資料準備腳本：`scripts/prepare_dataset.py`、`scripts/build_embedding_requests.py`。
- 已產出資料工件：`data/test_dataset_canonical.csv`、`data/prepared_examples.jsonl`、`data/embedding_requests_examples.jsonl`（20 筆）。
- 已完成可匯入 workflow 骨架：
	- `workflows/wf_inbox_classifier.json`
	- `workflows/wf_human_review_queue.json`
	- `workflows/wf_feedback_to_rag.json`
	- `workflows/wf_eval_runner.json`
	- `workflows/wf_error_handler.json`
- 已建立關鍵配置：`src/config/model_routing.json`、`src/config/confidence_policy.json`、`src/config/vector_indexes.json`。
- 已完成英文設計文件：`docs/email_classifier_full_design_en.md`；中文 full design 已移除。
- `README.md` 已更新且移除中文設計文件引用。

## 進行中
- 將 workflow 中的佔位 HTTP 端點替換為實際 embedding/vector/LLM 供應商端點與憑證。
- 以更大且人工覆核的驗證集校準 confidence 權重與閾值。

## 下一步
- 在 n8n 匯入 workflows 並完成 credentials 綁定。
- 建立 mock 或真實 API 端點的端到端測試，驗證分類、升級、回覆與錯誤流程。
- 補齊依賴清單（例如 `requirements.txt`）與最小 CI 驗證（JSON/腳本 smoke test）。

## 關鍵決策摘要
- 採雙軌策略：競賽可交付 MVP + 產品級安全機制（規則、信心閘門、HITL、錯誤處理）。
- 採 Tier1/Tier2 多層模型路由以平衡成本與品質。
- RAG 採 `examples` / `kb_policy` 雙索引隔離，禁止金標籤進入可檢索推論內容。
- 信心分數採組合公式與雙閾值閘門，低信心導向人工審核。
- 回饋回寫僅接受 `approved` 審核結果，避免資料污染。

## 已知問題與避雷
- 嚴禁將 `expected_category`、`expected_action` 寫入可檢索文本，避免標籤洩漏。
- 小樣本（目前 20 筆）只適合流程打通，不足以做穩定閾值定版。
- 未完成 provider wiring 前，workflow 為可匯入骨架，非最終可上線版本。

## 重要檔案
- `README.md`
- `docs/email_classifier_full_design_en.md`
- `docs/rag_embedding_strategy.md`
- `docs/implementation_runbook.md`
- `docs/decision-log.md`
- `workflows/wf_inbox_classifier.json`
- `src/config/confidence_policy.json`
- `scripts/prepare_dataset.py`

## 最近更新
- 日期：2026-03-05
- 內容：依競賽實作現況補齊 project memory；同步對齊 decision log 的架構與資料治理決策，並記錄中文 full design 已移除、README 引用已清理。
