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
- 官方 PDF 用語是 `pricing, support, security, setup, off-topic, etc.`；可推知最終 production 測試不應假設公開 seed set 已覆蓋所有情境，但也沒有公開證據顯示評測接受動態新增 category label。
- 回覆內容只能以 Nexus Integrations 官方文件/資源包為事實來源；不可臆測或超出文件作答。

## 官方評分與提交要求
- 評分為逐筆 0/1：
  - 1 分：分類正確，且回覆內容符合官方文件；或正確判定無法回答並升級給人工。
  - 0 分：分類錯誤、產生幻覺、漏掉重要資訊、或本該升級卻硬答。
- 官方明講：分類錯誤通常會導致回覆錯誤，因此分類本身就是高權重關鍵路徑。
- 官方提交後會用「沒看過的新郵件情境」直接打 production webhook，檢查泛化能力；不能只記住公開測資答案。
- 官方 PDF 原文是 `We'll trigger your production webhook with a POST request, sending new email scenarios your agent hasn't seen before`。
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
- 已依新版 `data/test_dataset.csv` 重建 `data/test_dataset_canonical.csv`，同步更新 canonical 衍生欄位與 `prepared_examples.jsonl` 的 eval labels。
- 已將 `data/*.csv` 全部正規化為 LF，並更新 `scripts/prepare_dataset.py` 讓後續 canonical CSV 輸出固定維持 LF。
- 已完成可匯入 workflow 骨架：
	- `workflows/wf_inbox_classifier.json`
	- `workflows/wf_human_review_queue.json`
	- `workflows/wf_feedback_to_rag.json`
	- `workflows/wf_eval_runner.json`
	- `workflows/wf_error_handler.json`
- 已建立關鍵配置：`src/config/model_routing.json`、`src/config/confidence_policy.json`、`src/config/vector_indexes.json`。
- 已新增 `src/config/structured_knowledge.json`，定義 structured lookup contract 與 per-category source policy。
- 已完成英文設計文件：`docs/email_classifier_full_design_en.md`；中文 full design 已移除。
- `README.md` 已更新且移除中文設計文件引用。
- 已將 unseen-case 防禦 heuristic 落入主流程：
  - retrieval novelty signals（低 `sim_top1`、小 margin、低 rerank、top-K 類別分裂）
  - classifier / retrieval disagreement gate
  - secondary intent 與 `risk_tags` 輔助升級
  - per-category auto-reply / human-review thresholds
  - KB evidence sufficiency gate（證據數量與 top score 不足時改走人工）
- 已將主流程調整為 structured-first、RAG-limited：
  - `examples` 只用於分類相似度，不作為回覆事實來源
  - `structured facts lookup` 優先承接 pricing / capability / routing 類資訊
  - `kb_policy` 改為敘述性文件證據與 fallback
- 已完成 code review 修正（共 5 項 + 1 措辭）：
  - `Assess Structured Facts` 正確更新 `needs_escalation`
  - structured-only 路徑改走 `Grounding Requires Review?` gate
  - 下游節點改用 `$('Node').item.json` 引用上游，不再依賴 API echo
  - `Http_StructuredLookup` 加入 `continueOnFail` 與 error fallback
  - `Code_ParseClassifier` 加入 SYNC 註解標記 `knowledgePolicies` 同步需求
  - `reply_system_prompt.md` 措辭統一為 grounding evidence
- 已在 `wf_inbox_classifier` 前段加入顯式 merge 保留 context：
  - `Http_Embed` 後新增 `Merge Embed Context`
  - `Http_RetrieveExamples` 後新增 `Merge Retrieval Context`
  - 前段 retrieval/confidence 鏈路改為顯式合併原始 email item 與 HTTP response，避免 `from`、`subject`、`body`、`query_text`、`is_high_risk` 在中途遺失

## 進行中
- 將 workflow 中的佔位 HTTP 端點替換為實際 embedding/vector/LLM/structured lookup 供應商端點與憑證。
- 以更大且人工覆核的驗證集校準 confidence 權重與閾值。
- 將現有實作補齊為符合競賽提交格式的成品，包括 production webhook、匯出 JSON 與 demo 流程。

## 下一步
- 在 n8n 匯入 workflows 並完成 credentials 綁定。
- 建立 mock 或真實 API 端點的端到端測試，驗證分類、structured lookup、文件 fallback、升級與錯誤流程。
- 補齊依賴清單（例如 `requirements.txt`）與最小 CI 驗證（JSON/腳本 smoke test）。
- 以官方會送「未知新案例」為前提，驗證 workflow 是否具備泛化與正確升級能力，而不是只對現有測資調參。
- 準備最終提交資產：production webhook URL、workflow JSON export、60 秒 demo 影片。

## 關鍵決策摘要
- 採雙軌策略：競賽可交付 MVP + 產品級安全機制（規則、信心閘門、HITL、錯誤處理）。
- 採 Tier1/Tier2 多層模型路由以平衡成本與品質。
- RAG 採 `examples` / `kb_policy` 雙索引隔離，禁止金標籤進入可檢索推論內容。
- 知識來源採 structured-first、RAG-limited：可結構化事實先走 structured lookup，`kb_policy` 僅負責敘述性文件證據與 fallback。
- workflow 資料保留策略採混合式：前段多節點共用 context 時優先用 Merge node 顯式合併，後段 localized 依賴則可用 `$('Node').item.json` 直接引用上游。
- 信心分數採組合公式與雙閾值閘門，低信心導向人工審核。
- 最終自動回覆判斷不只看 retrieval confidence，還必須同時通過 category confidence、risk gate 與 KB evidence sufficiency gate。
- 回饋回寫僅接受 `approved` 審核結果，避免資料污染。
- 對 unseen / open-set email 的處理策略是固定 primary taxonomy + 保守升級；以 `needs_escalation`、`risk_tags`、`secondary_categories` 承接未知或混合意圖，而不是在線上發明新 category。

## 已知問題與避雷
- 嚴禁將 `expected_category`、`expected_action` 寫入可檢索文本，避免標籤洩漏。
- 小樣本（目前 20 筆）只適合流程打通，不足以做穩定閾值定版。
- 未完成 provider wiring 前，workflow 為可匯入骨架，非最終可上線版本。
- 官方會在提交後用新案例測 production webhook；任何只對公開測資做模板化或記憶化的設計都有高風險失分。
- 若 classifier 對新型 email 產生 taxonomy 外 label，應視為 prompt / parser 偏移而非功能需求；需修正回固定 taxonomy 契約。
- 回覆若超出 Nexus 文件可支持的內容，寧可升級人工也不要硬答；錯誤自信回覆是官方明確打 0 的情境。
- `structured facts lookup` 若沒有明確來源版本與 audit log，仍可能退化成另一個黑箱；正式 provider 需保留 `fact_id`、來源與生效時間。
- 需保留可對外展示的提交形態，不只是在本地跑 eval；最終要能提供 production webhook 與 demo 影片。
- 新增的 per-category thresholds 與 novelty/evidence gate 目前仍屬 heuristic default，必須用更多人工覆核樣本做 calibration，否則可能過度升級。

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
- `src/config/structured_knowledge.json`
- `scripts/prepare_dataset.py`

## 最近更新
- 日期：2026-03-15
- 內容：重新核對本地官方 PDF，確認 final evaluation 會以 `new email scenarios your agent hasn't seen before` 打 production webhook，且分類描述為 `pricing, support, security, setup, off-topic, etc.`；因此補充 repo 決策為固定 taxonomy + 保守升級，不採動態新增 category。
- 日期：2026-03-15
- 內容：`test_dataset.csv` 更新後，已重建 `test_dataset_canonical.csv` 與 `prepared_examples.jsonl`，使共同欄位與新版測資一致；同時把 `data/*.csv` 全部轉成 LF，並調整 `scripts/prepare_dataset.py` 讓後續輸出固定採 LF。
- 日期：2026-03-13
- 內容：在 `wf_inbox_classifier` 前段加入 `Merge Embed Context` 與 `Merge Retrieval Context`，顯式保留 email context 穿越 embedding / example retrieval HTTP 鏈路；後半段則維持必要的 upstream reference，避免過度堆疊 merge node。
- 日期：2026-03-13
- 內容：Code review 修正 structured-first workflow 的 5 項問題（needs_escalation bug、review gate bypass、context echo 依賴、error fallback、knowledge policy 同步），並統一 prompt 措辭。
- 日期：2026-03-13
- 內容：將知識路由調整為 structured-first、RAG-limited；新增 `src/config/structured_knowledge.json`，更新設計文件、runbook、prompt 與 workflow，讓 `structured facts lookup` 優先承接 pricing/security capability 類事實，`kb_policy` 改為敘述性文件 fallback。
- 日期：2026-03-09
- 內容：整理官方 Notion 挑戰總覽與案例題需求，並將 unseen-case 防禦 heuristic 實作到 workflow/config/prompt：加入 novelty signals、類別化閾值、classifier/retrieval disagreement gate、multi-intent `risk_tags` 與 KB evidence sufficiency gate。
