# Structured Facts + Retrieval Strategy

## Goal
Use the seed dataset for similarity-based classification while shifting deterministic business knowledge toward structured lookup.

## Source Design
1. `examples` namespace
   - Purpose: intent similarity hints for classification
   - Embed: `subject_clean + body_clean + sender_domain`
   - Do not embed: `expected_category`, `expected_action`
2. Structured lookup tool
   - Purpose: authoritative facts for pricing, capability, routing, and policy matrices
   - Request contract: defined in `src/config/structured_knowledge.json`
   - Expected response: explicit facts, coverage, answerability, and source references
3. `kb_policy` namespace
   - Purpose: narrative grounding and policy excerpts when structured facts are insufficient or procedural wording matters
   - Embed: official Nexus docs, FAQ, setup guides, security / pricing / legal policy snippets

## Retrieval Flow
1. Embed incoming email query.
2. Retrieve top-k from `examples` for classification context.
3. Compute confidence using similarity + margin + rerank score.
4. Classify with Tier 1 or Tier 2 LLM.
5. Call structured lookup based on the predicted category.
6. If structured coverage is insufficient or the category requires document evidence, retrieve from `kb_policy`.
7. Reply only from the final `grounding_evidence` set, or escalate.

## Confidence Formula
`0.50*sim_top1 + 0.30*(sim_top1-sim_top2) + 0.20*rerank_score`

## Update Policy
- Only human-reviewed outcomes are appended to the `examples` index.
- Keep immutable raw logs and separate reviewed dataset.
- Do not auto-write back into structured facts or `kb_policy`.
- Run incremental re-embedding on schedule (daily / weekly) only for similarity and document indexes.

## Cost Strategy
- Default: lower-cost model tier for classification.
- Upgrade to stronger model for legal / security / compliance or low-confidence cases.
- Cache embeddings by text hash.
- Avoid document retrieval when structured facts already provide sufficient evidence for safe auto-reply.
