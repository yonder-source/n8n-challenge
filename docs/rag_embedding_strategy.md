# RAG + Embedding Strategy

## Goal
Use the seed dataset for intent similarity while preventing label leakage and overfitting.

## Index Design
1. `examples` namespace
   - Purpose: intent similarity hints
   - Embed: `subject_clean + body_clean + sender_domain`
   - Do not embed: `expected_category`, `expected_action`
2. `kb_policy` namespace
   - Purpose: grounded reply generation
   - Embed: official Nexus docs, FAQ, security/pricing/legal policy snippets

## Retrieval Flow
1. Embed incoming email query.
2. Retrieve top-k from `examples` for classification context.
3. Compute confidence using similarity + margin + rerank score.
4. If confidence is high, classify directly; otherwise escalate or invoke stronger LLM tier.
5. Retrieve evidence from `kb_policy` for reply drafting.

## Confidence Formula
`0.50*sim_top1 + 0.30*(sim_top1-sim_top2) + 0.20*rerank_score`

## Update Policy
- Only human-reviewed outcomes are appended to `examples` index.
- Keep immutable raw logs and separate reviewed dataset.
- Run incremental re-embedding on schedule (daily/weekly).

## Cost Strategy
- Default: lower-cost model tier for classification.
- Upgrade to stronger model for legal/security/compliance or low confidence cases.
- Cache embeddings by text hash.
