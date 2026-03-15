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

### [2026-03-15] 對 unseen email 採固定 taxonomy + 保守升級，不動態產生新 category
- 背景：官方 PDF 明確寫到提交後會以 `new email scenarios your agent hasn't seen before` 直接打 production webhook；同時分類描述為 `pricing, support, security, setup, off-topic, etc.`，表示公開 seed set 不是封閉題庫，但也未提供開放式新 label 的評測契約。
- 決策：production 輸出維持固定 primary taxonomy；遇到新型、混合或無法穩定貼標的 email，不在線上動態建立新 category，而是映射到最接近且安全的既有類別，並以 `needs_escalation`、`risk_tags`、`secondary_categories`、route team 表達不確定性與後續路由。
- 原因：競賽重點是對未見案例保持 grounded 與保守，而不是發明新 taxonomy；若輸出 schema 外 label，存在 eval / judge 不認列的風險。
- 影響：workflow 與 prompts 應明確禁止 inventing new categories；文件需說明 unseen email 的主要處理策略是 novelty detection + human review，而不是 category expansion。
- 替代方案：採 open-set dynamic category generation（不採用，競賽評測契約不明、可比性差、風險高）。
- 狀態：Accepted

### [2026-03-13] 在前段 HTTP 鏈路加入 Merge 節點保留 email context
- 背景：`Embed Query -> Retrieve Examples -> Compute Confidence` 前段會經過多個 `HTTP Request` 節點；若只依賴 response body 往下傳，原始 email 欄位與風險訊號可能在中途遺失。
- 決策：在 `Http_Embed` 後加入 `Merge Embed Context`，在 `Http_RetrieveExamples` 後加入 `Merge Retrieval Context`，用 position-based combine 將原始上游 item 與 HTTP response 明確合併；後半段 localized 依賴則維持 `$('Node').item.json` 直接引用。
- 原因：前段多個後續節點都需要原始 email context，顯式 merge 比分散的 upstream reference 更穩、更容易在 n8n UI debug；但若整條 workflow 到處加 merge node，會增加視覺噪音與維護成本。
- 影響：`wf_inbox_classifier` 的前段資料流改為顯式保留 `from/subject/body/query_text/is_high_risk` 等欄位，`Code_ExtractEmbedding` 也改為從 merge 後 item 取值；後續 smoke test 需確認 n8n 實跑時 item count 與 combine-by-position 行為符合預期。
- 替代方案：全程只用 `$('Node').item.json` 回抓上游（不採用，前段多節點重複依賴原始 context 時可讀性與穩定性較差）。
- 狀態：Accepted

### [2026-03-13] Code review 修正：structured-first workflow 安全性強化
- 背景：對 structured-first 變更做 code review 後發現 5 項問題（1 bug、2 設計缺陷、2 中風險）。
- 決策：一次性修復全部問題。
- 修正項目：
  1. Bug: `Assess Structured Facts` 未更新 `needs_escalation`，導致 structured-only 路徑可能跳過升級。
  2. Design: structured-only 路徑繞過 `Grounding Requires Review?` gate；改為所有路徑都經過同一 review gate。
  3. Design: 下游節點依賴 API echo 回傳 `context`；改用 `$('Parse Classifier').item.json` 與 `$('Assess Structured Facts').item.json` 直接引用上游。
  4. Medium: `knowledgePolicies` 在 workflow 和 `structured_knowledge.json` 重複定義；加入 SYNC 註解。
  5. Medium: structured lookup HTTP 失敗時 workflow 直接中斷；加入 `continueOnFail` 並在 assess 節點偵測 `$json.error` 做 graceful fallback。
- 附帶修正：`reply_system_prompt.md` rule 2 措辭統一為 grounding evidence。
- 狀態：Accepted

### [2026-03-13] 採用 structured-first、RAG-limited 的知識路由
- 背景：challenge 要求回覆必須 grounded 且對 unseen case 保守；若把 pricing、capability、routing policy 這類可結構化資料完全交給 RAG，chunking / metadata / recall 會增加黑箱性與追溯成本。
- 決策：保留 `examples` 與 `kb_policy` 雙索引，但將主流程改為 `structured facts lookup -> 視需要才進 kb_policy retrieval`；其中 `examples` 只用於分類相似度，`structured facts` 優先承接 pricing / security capability 等可驗證事實，`kb_policy` 退為敘述性文件證據與 fallback。
- 原因：這樣較符合官方「根據文件/官方資料作答，證據不足就升級人工」的評分邏輯，也更容易做 audit trail、source attribution 與失敗分析。
- 影響：workflow 新增 structured lookup 節點與來源路由欄位，需額外維護 `src/config/structured_knowledge.json` 與 `STRUCTURED_LOOKUP_URL` 合約；文件與 prompt 也同步改為 hybrid grounding。
- 替代方案：維持 retrieval-first、把大部分知識都放在 `kb_policy` 向量檢索（不採用，對 deterministic facts 的可追溯性與穩定性較差）。
- 狀態：Accepted

### [2026-03-09] 採用三段 gate 與類別化閾值來處理 unseen email
- 背景：官方會在提交後用未見過的新郵件情境直接呼叫 production webhook；原本只有 retrieval-based confidence 與單一全域閾值，對 distribution shift 防禦不足。
- 決策：自動回覆改為同時檢查 `category confidence`、`risk / disagreement gate`、`KB evidence sufficiency`；並針對不同 category 使用不同 auto-reply / review thresholds。
- 原因：未知案例最常失手的不是單純相似度低，而是多意圖、檢索與分類器不一致、或文件證據其實不足卻硬答。
- 影響：整體流程會更保守，人工審核量可能上升，但可顯著降低 hallucination、誤分類後誤答、與文件外回答的風險。
- 替代方案：延用單一公式與全域閾值（不採用，對 unseen case 的防禦面不夠）。
- 狀態：Accepted

### [2026-03-09] 以官方 challenge brief 作為交付範圍與驗收基準
- 背景：既有專案記憶偏重 workflow 架構、RAG 與資料治理，但缺少競賽官方對 deliverables、評分方式與提交後驗證流程的摘要。
- 決策：後續設計、實作與驗證一律以官方 Notion challenge brief 與 Nexus Integrations case study 為準，交付物需覆蓋 email agent、evaluation system、production webhook URL、workflow JSON export 與 60 秒 demo。
- 原因：競賽不是只看本地測資是否可跑通；官方會以未見過的新情境直接呼叫 production webhook，重點是 grounded reply、正確分類、必要時升級人工，以及長期可驗證性。
- 影響：後續 agent 必須優先避免針對公開測資過度擬合，並把泛化能力、評測流程與最終提交資產視為一級需求。
- 替代方案：只以目前 repo 的技術骨架為主線繼續開發（不採用，容易偏離官方成功條件）。
- 狀態：Accepted

### [2026-03-05] 採用雙軌策略：競賽可交付 MVP + 產品級安全機制
- 背景：競賽要求可運作的郵件分類自動化，同時真實場景需控制幻覺、誤判與升級風險。
- 決策：主流程以可評測 MVP 為核心，並同時納入規則前置、信心閘門、HITL、人工作業回寫、錯誤處理等產品級機制。
- 原因：只做單一 LLM 難以兼顧分數與營運風險；雙軌可同時滿足短期評測與可擴充上線。
- 影響：工作流節點與配置較多，但可逐步啟閉功能，不影響基線跑分。
- 替代方案：純單模型直推（不採用，成本與風險不可控）。
- 狀態：Accepted

### [2026-03-05] 採用多層模型路由（Tier1/Tier2）控成本與品質
- 背景：分類場景存在簡單與高風險樣本，單一模型會造成成本浪費或品質不足。
- 決策：先以關鍵字/規則與檢索信號做路由，低風險走 Tier1，高風險或低信心走 Tier2。
- 原因：將高成本推理集中在不確定案例，提升整體效益。
- 影響：需維護 `src/config/model_routing.json` 並持續校正關鍵字與閾值。
- 替代方案：固定使用高階模型（不採用，成本不穩定）。
- 狀態：Accepted

### [2026-03-05] RAG 採雙索引隔離並禁止標籤洩漏
- 背景：競賽資料含 `expected_category/expected_action`，若直接入檢索內容會造成標籤洩漏。
- 決策：向量索引拆分為 `examples` 與 `kb_policy`；推論可檢索內容不得包含金標籤；金標僅用於評測與監督學習。
- 原因：避免資料污染，維持評測公平與線上可解釋性。
- 影響：資料準備與回寫流程需區分可檢索欄位與評測欄位。
- 替代方案：單一索引混存（不採用，洩漏風險高）。
- 狀態：Accepted

### [2026-03-05] 信心分數採組合式公式並以閘門決策自動化程度
- 背景：僅看 top1 相似度容易誤判，需可調且可解釋的自動化依據。
- 決策：使用 `0.50*sim_top1 + 0.30*(sim_top1-sim_top2) + 0.20*rerank_score`，並設 `auto_reply=0.78`、`human_review=0.60` 閾值。
- 原因：同時考慮主匹配強度、與次佳差距、重排品質，可降低錯誤自動回覆。
- 影響：需以更大驗證集做後續校準。
- 替代方案：單一閾值規則（不採用，穩定性不足）。
- 狀態：Accepted

### [2026-03-05] 人工審核回饋僅回寫已核准樣本至 examples 索引
- 背景：錯誤標記若直接回寫會放大偏差，造成長期退化。
- 決策：`wf_feedback_to_rag` 只處理 `approved` 審核結果並記錄審計資訊。
- 原因：降低污染風險，維持資料品質閉環。
- 影響：需維護審核佇列與回寫審計紀錄。
- 替代方案：全量自動回寫（不採用，品質不可控）。
- 狀態：Accepted

### [2026-03-05] 以本地優先開發，工作流輸出為可匯入 n8n JSON 骨架
- 背景：目前以本地開發與驗證為主，外部 API 憑證與端點尚未完全固定。
- 決策：先交付可匯入的 workflow JSON 骨架與可執行資料前處理腳本，再進行端點綁定。
- 原因：先鎖定流程結構與資料契約，可降低後續整合返工。
- 影響：仍需補齊實際 provider credentials 與 endpoint wiring。
- 替代方案：先綁定單一供應商後再設計流程（不採用，耦合過早）。
- 狀態：Accepted

### [2026-03-05] 建立專案長期記憶機制
- 背景：多輪開發時，對話上下文不會永久保留，容易重複前情提要。
- 決策：建立 `docs/project-memory.md` 與 `docs/decision-log.md`，並在 `AGENTS.md` 規範每次任務前先讀取。
- 原因：降低溝通成本，保留可追溯的決策脈絡。
- 影響：每次交付後需額外維護少量文件。
- 替代方案：僅依賴對話紀錄（不採用，跨 session 易遺失脈絡）。
- 狀態：Accepted
