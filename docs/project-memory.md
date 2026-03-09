# Project Memory

## 目前目標
- 交付可匯入 n8n 的競賽級 Email Classifier 工作流，並保留可產品化的安全與擴充設計。
- 在不造成標籤洩漏前提下，完成可評測的資料準備、檢索與信心決策鏈路。
- 交付內容需直接對齊 n8n Community Challenge「AI Agents with Evals」與案例題「Inbox Inferno at Nexus Integrations」的官方要求，而不只是做出可運作的分類 demo。

## 競賽任務摘要
- 競賽主題是為虛構公司 Nexus Integrations 建立可信任的 AI email agent；核心問題不是單次跑通，而是長期維持正確、可評測、可監控。
- 角色背景：Nexus Integrations 約 80 人，銷售企業整合軟體；共享收件匣每天收到大量郵件，重複性高，但錯答成本也高。
- 業務痛點：Jacob 擔心 AI「更快地答錯」以及 prompt、model、文件變動後品質悄悄退化，因此官方要求一定要把 evaluations 一起做進方案。
- 官方要求的系統分兩部分：
  - Email agent：接收 email webhook、分類郵件、根據 Nexus 文件產生回覆草稿。
  - Evaluation system：用 n8n AI Evaluation 功能或等效流程，把測試案例逐筆跑過並由 LLM judge 以 0/1 評分。
- Email agent 的 webhook 輸入格式為 `from`、`subject`、`body`；輸出至少要有 `category` 與 `draft_reply`。
- 分類需能區分 `pricing`、`support`、`security`、`setup`、`off-topic` 等類型，且不同類型回覆策略不同。
- 回覆內容只能以 Nexus Integrations 官方文件/資源包為事實來源；不可臆測或超出文件作答。

## 官方評分與提交要求
- 評分為逐筆 0/1：
  - 1 分：分類正確，且回覆內容符合官方文件；或正確判定無法回答並升級給人工。
  - 0 分：分類錯誤、產生幻覺、漏掉重要資訊、或本該升級卻硬答。
- 官方明講：分類錯誤通常會導致回覆錯誤，因此分類本身就是高權重關鍵路徑。
- 官方提交後會用「沒看過的新郵件情境」直接打 production webhook，檢查泛化能力；不能只記住公開測資答案。
- 競賽提交物除 workflow 本身外，還需要：
  - production webhook URL
  - workflow JSON export
  - 60 秒 demo 影片
- 官方頁面標示的本月截止日是 `2026-03-22`。
- 社群溝通主通道是 Discord，官方公告與資源更新會在那裡發布。

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
- 將現有實作補齊為符合競賽提交格式的成品，包括 production webhook、匯出 JSON 與 demo 流程。

## 下一步
- 在 n8n 匯入 workflows 並完成 credentials 綁定。
- 建立 mock 或真實 API 端點的端到端測試，驗證分類、升級、回覆與錯誤流程。
- 補齊依賴清單（例如 `requirements.txt`）與最小 CI 驗證（JSON/腳本 smoke test）。
- 以官方會送「未知新案例」為前提，驗證 workflow 是否具備泛化與正確升級能力，而不是只對現有測資調參。
- 準備最終提交資產：production webhook URL、workflow JSON export、60 秒 demo 影片。

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
- 官方會在提交後用新案例測 production webhook；任何只對公開測資做模板化或記憶化的設計都有高風險失分。
- 回覆若超出 Nexus 文件可支持的內容，寧可升級人工也不要硬答；錯誤自信回覆是官方明確打 0 的情境。
- 需保留可對外展示的提交形態，不只是在本地跑 eval；最終要能提供 production webhook 與 demo 影片。

## 來源摘要
- 挑戰總覽：`https://n8n.notion.site/AI-Agents-with-Evals-30c5b6e0c94f818e9d62cb4894727ff9`
- 案例題頁面：`https://n8n.notion.site/Inbox-Inferno-at-Nexus-Integrations-AI-Evals-30e5b6e0c94f80a499a8e33ae028199a`

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
- 日期：2026-03-09
- 內容：整理官方 Notion 挑戰總覽與案例題需求，補充競賽目標、評分規則、提交物、截止日與泛化/升級避雷，讓後續 agent 能直接理解這個 challenge 的成功條件。
