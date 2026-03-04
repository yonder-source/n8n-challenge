# Email Classifier Full Design Document (Beginner-Friendly)

## 1. What problem does this system solve?

Incoming emails can vary widely:
- Technical setup questions (Setup)
- Security or legal questions (Security / Legal)
- Pricing and commercial inquiries (Pricing / Partnership)
- Emails that don't belong in support (Misdirected / Spam)

Reading and routing everything manually is slow and costly. Sending everything to a single AI without safeguards risks misclassification, hallucination, and incorrect replies for high-risk cases.

This system aims to:
1) Classify each email into a category.
2) Decide whether to auto-reply or escalate to a human.
3) Ensure replies are grounded in verified knowledge (RAG).
4) Use human-reviewed results to improve the system in a controlled way.

---

## 2. System overview (four pipelines)

1. Main classification pipeline: `wf_inbox_classifier`
   - Receive → Clean → Fast-rule filter → Vector retrieval → LLM classification → Confidence gate → Auto-reply or human queue

2. Human review pipeline: `wf_human_review_queue`
   - Create review ticket for low-confidence or high-risk cases and notify reviewers

3. Feedback-to-RAG pipeline: `wf_feedback_to_rag`
   - Only human-approved examples are added back to the `examples` vector index

4. Error handling pipeline: `wf_error_handler`
   - Centralized handling for timeouts, rate limits, and permanent failures with alerts

---

## 3. Why a dual-index RAG (instead of one index)?

### 3.1 `examples` index (example similarity)
- Purpose: help determine which category an incoming email most closely matches
- Stored content: `subject_clean + body_clean + sender_domain`
- Do NOT store gold labels (`expected_category` / `expected_action`) in the retrievable text used for generation

### 3.2 `kb_policy` index (grounding for replies)
- Purpose: provide authoritative knowledge and policies for drafting replies
- Stored content: official product docs, security guidelines, pricing policy excerpts, and legal snippets

### 3.3 Why separate indexes?
- Prevents label leakage (the model shouldn't copy gold labels from examples as answers)
- Avoids inflated offline scores that don't generalize to unseen cases
- Enables traceable, evidence-backed replies and reduces hallucination risk

---

## 4. End-to-end flow (step by step)

### Step A. Ingest & clean
- Entry point: Webhook receives `from`, `subject`, `body`
- Cleaning includes:
  - stripping `Re:`/`Fwd:` prefixes
  - collapsing extra whitespace
  - truncating body to a safe token limit
  - extracting `sender_domain`

### Step B. Regex fast-path (high-precision, low-cost)
- Handle clearly identifiable cases (e.g., bank statements, spam recruiters)
- If a fast-rule matches, return result immediately without calling LLMs

Benefits: fast, cheap, deterministic

### Step C. Embedding + retrieval
- Create an embedding for the cleaned email text
- Retrieve top-K similar examples from the `examples` index
- Extract `sim_top1`, `sim_top2`, and rerank scores for the best candidates

### Step D. Compute confidence score

Formula:

`score = 0.50*sim_top1 + 0.30*(sim_top1 - sim_top2) + 0.20*rerank_score`

### Step E. Tiered LLM routing
- If high-risk category or low confidence → route to Tier 2 (stronger, more expensive model)
- Otherwise → use Tier 1 (cheaper model)

### Step F. Auto-reply vs human review
- High-confidence and not high-risk → generate a reply
- Low-confidence or high-risk → queue for human review (`wf_human_review_queue`)

### Step G. Reply generation (grounded only on `kb_policy`)
- Retrieve policy evidence from `kb_policy`
- Use evidence-only prompt to generate `draft_reply`
- Output schema: `category`, `draft_reply`, `confidence`, `needs_escalation`, `route_team`, `evidence_refs`

---

## 5. Confidence formula explained (detailed)

### 5.1 What is `sim_top1`?
`sim_top1` is the vector similarity score of the most similar example retrieved from `examples` (typically normalized between 0 and 1 by the vector store).

Intuition:
- Closer to 1: the incoming email is very similar to a known example
- Closer to 0: there is little similarity to known examples

### 5.2 What is `sim_top2`?
`sim_top2` is the similarity score of the second-best retrieved example.

Why include it?
- If `top1` and `top2` are close (e.g., 0.88 vs 0.86), the case is ambiguous and less reliable for auto-decisions
- A gap between `top1` and `top2` indicates a clearer match

Thus `sim_top1 - sim_top2` is the *margin*.

### 5.3 What is `rerank_score`?
The first retrieval is a nearest-neighbor search (fast but approximate). A reranker (a cross-encoder or LLM-based scorer) provides a finer-grained quality score for the top candidates. `rerank_score` captures that refined judgement.

### 5.4 Why weights 0.50 / 0.30 / 0.20?

- `0.50 * sim_top1`:
  - The primary semantic match is the most stable signal, so it receives the largest influence.
  - It represents the system's baseline trust in the single best example.

- `0.30 * (sim_top1 - sim_top2)`:
  - This margin term penalizes ambiguity when two candidate examples are similarly close.
  - It reduces confidence when the decision boundary is fuzzy.

- `0.20 * rerank_score`:
  - Reranking is a valuable secondary check but can be more variable (dependent on prompt and model).
  - Giving it 0.20 helps improve precision without letting reranker noise dominate.

### 5.5 Why not `0.40 * sim_top1`?
Reducing `sim_top1`’s weight to 0.40 would relatively elevate the margin and rerank terms. That can cause:

1. Conservative behavior: some clearly-matching emails might fall below the auto-reply threshold due to rerank variance and be unnecessarily escalated
2. Lower decision stability: with a small dataset, rerank variance can cause larger swings in final scores

Using 0.50 is a conservative default that prioritizes the strongest semantic match while still accounting for ambiguity and rerank signals. We recommend calibrating these weights with a larger labeled validation set.

### 5.6 Thresholds
- `auto_reply = 0.78`: scores above this threshold can be automatically replied to
- `human_review = 0.60`: scores below this threshold go to human review
- 0.60–0.78: intermediate zone; typically routed to human review for high-risk categories

These thresholds are starting points and should be tuned on validation data.

---

## 6. Cost-control design (why this saves money)

1. Apply low-cost deterministic regex rules first to handle obvious cases
2. Default to Tier 1 (cheaper model) for most classification
3. Promote to Tier 2 only for low confidence or high-risk cases
4. Cache embeddings by text hash to avoid recomputation

This approach is far cheaper than using the top-tier model for every message.

---

## 7. Human-in-the-loop (HITL)

Low-confidence and high-risk cases must be human-reviewed because:
- Security/legal mistakes are costly
- Missing an escalation in evaluation costs you points

Only reviewer-approved examples are appended to the `examples` index to avoid feeding incorrect labels into retrievable data.

---

## 8. Error handling (production essentials)

`wf_error_handler` performs three tasks:
1. Classify transient errors (timeouts, 429s) versus permanent failures
2. Retry transient errors with exponential backoff
3. Move permanent errors to a dead-letter queue and alert ops

This prevents silent workflow failures and enables timely operator intervention.

---

## 9. Key files in this repository

- Main workflow: `workflows/wf_inbox_classifier.json`
- Human review: `workflows/wf_human_review_queue.json`
- Feedback to RAG: `workflows/wf_feedback_to_rag.json`
- Error handler: `workflows/wf_error_handler.json`
- Confidence policy: `src/config/confidence_policy.json`
- Model routing: `src/config/model_routing.json`
- Vector index config: `src/config/vector_indexes.json`

---

## 10. Calibration and optimization (next steps)

1. Collect at least 100 human-reviewed examples
2. Grid-search weights and thresholds, for example testing:
   - `sim_top1` in {0.40, 0.45, 0.50, 0.55}
   - `margin` weight in {0.20, 0.25, 0.30, 0.35}
   - `rerank` weight in {0.10, 0.15, 0.20, 0.25}
3. Evaluate using macro-F1, escalation precision/recall, and cost per email
4. Choose the weight configuration that balances accuracy and cost

---

## 11. One-line summary

This design uses a transparent multi-signal confidence score to let AI automatically handle the majority of emails while safely routing uncertain or high-risk cases to humans, and then feeding validated outcomes back into the system for controlled continuous improvement.
