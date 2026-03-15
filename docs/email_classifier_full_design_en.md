# Email Classifier Full Design Document (Beginner-Friendly)

## 1. What problem does this system solve?

Incoming emails can vary widely:
- Technical setup questions (Setup)
- Security or legal questions (Security / Legal)
- Pricing and commercial inquiries (Pricing / Partnership)
- Emails that do not belong in support (Misdirected / Spam)

The official challenge wording uses `pricing, support, security, setup, off-topic, etc.` and says the final webhook test will use new email scenarios the agent has not seen before. That means the system should handle unseen cases conservatively, but still stay within a fixed primary taxonomy for production output.

The challenge is not only classification accuracy. The system must also avoid hallucinations, stay grounded in official Nexus material, and escalate when evidence is weak.

This system aims to:
1. Classify each email into a category.
2. Decide whether to auto-reply or escalate to a human.
3. Prefer structured facts for deterministic business data.
4. Use document retrieval only when narrative evidence is needed.
5. Feed only human-approved examples back into similarity memory.

---

## 2. System overview (four pipelines)

1. Main classification pipeline: `wf_inbox_classifier`
   - Receive -> Clean -> Fast-rule filter -> Example retrieval -> LLM classification -> Structured facts lookup -> Optional document retrieval -> Auto-reply or human queue

2. Human review pipeline: `wf_human_review_queue`
   - Create review ticket for low-confidence or high-risk cases and notify reviewers

3. Feedback-to-examples pipeline: `wf_feedback_to_rag`
   - Only human-approved examples are added back to the `examples` similarity index

4. Error handling pipeline: `wf_error_handler`
   - Centralized handling for timeouts, rate limits, and permanent failures with alerts

---

## 3. Why a three-layer knowledge design?

### 3.1 `examples` index (similarity only)
- Purpose: provide category hints from historical reviewed emails
- Stored content: `subject_clean + body_clean + sender_domain`
- Never use this index as the source of truth for reply facts

### 3.2 Structured facts lookup (primary source for deterministic facts)
- Purpose: answer questions that should come from stable records instead of chunked text
- Typical content:
  - pricing plans and handoff policy
  - supported integrations / capability matrices
  - security capability registry
  - routing policy by category
- Benefits:
  - easier audit trail
  - explicit request / response logs
  - better traceability than relying on chunk recall alone

### 3.3 `kb_policy` index (document evidence fallback)
- Purpose: retrieve official document excerpts when wording, caveats, or procedural guidance matter
- Typical content:
  - setup guides
  - policy snippets
  - legal / security guidance that must remain grounded in official text

### 3.4 Why combine them?
- Structured facts are better for deterministic lookup.
- Document retrieval is still useful for narrative explanation and policy wording.
- Separating the roles reduces hallucination risk and improves debugging.

---

## 4. End-to-end flow (step by step)

### Step A. Ingest and clean
- Entry point: webhook receives `from`, `subject`, `body`
- Cleaning includes:
  - stripping `Re:` / `Fwd:` prefixes
  - collapsing extra whitespace
  - truncating body to a safe token limit
  - extracting `sender_domain`

### Step B. Regex fast-path
- Handle clearly identifiable cases such as spam recruiter outreach or wrong-recipient emails
- If a fast-rule matches, return immediately without LLM or retrieval

### Step C. Example retrieval for classification
- Create an embedding for the cleaned email text
- Retrieve top-K similar examples from the `examples` index
- Use similarity only as a classification signal, not as reply grounding

### Step D. Compute classification confidence

`score = 0.50*sim_top1 + 0.30*(sim_top1 - sim_top2) + 0.20*rerank_score`

### Step E. Tiered LLM classification
- If high-risk or low-confidence -> use Tier 2
- Otherwise -> use Tier 1
- Output category, risk tags, route team, escalation signal, and confidence
- If the email does not fit cleanly, map it to the closest safe taxonomy category and escalate instead of inventing a new label

### Step F. Structured-first grounding
- After category selection, call the structured lookup tool
- Use category policy to decide:
  - whether structured facts are required
  - whether document retrieval is still needed
  - which fact sets are expected

### Step G. Optional document retrieval
- If structured facts are missing, incomplete, or the category requires narrative evidence, retrieve from `kb_policy`
- Run a separate sufficiency gate before allowing auto-reply

### Step H. Reply generation
- Draft the reply from `grounding_evidence` only
- `grounding_evidence` may contain:
  - structured facts
  - document evidence
  - or both
- If evidence is insufficient, acknowledge and escalate instead of guessing

---

## 5. When do we use structured facts vs document retrieval?

### Structured-first categories
- `Pricing Question`
  - pricing tables, packaging, sales handoff, enterprise quote policy
- `Security Question`
  - capability matrix, supported controls, review routing, trust-policy registry

### Hybrid categories
- `Setup Question`
  - structured facts for supported integrations / prerequisites
  - document retrieval for procedural steps and troubleshooting guidance

### Review-only categories
- `Billing / Finance`
- `Contract / Legal`
- `Legal / Compliance`
- `Job Application / HR`
- `Partnership / Business Development`

These categories are typically escalated regardless of retrieval quality because the business risk is high.

---

## 6. Confidence formula explained

### 6.1 What is `sim_top1`?
The similarity score of the most similar reviewed example.

### 6.2 What is `sim_top2`?
The similarity score of the second-best example. The gap between them measures ambiguity.

### 6.3 What is `rerank_score`?
A refined quality signal from reranking the top retrieved candidates.

### 6.4 Why keep retrieval in the loop?
Because example similarity still helps classification on unseen emails.
The key change is role separation:
- retrieval for category hints
- structured facts for deterministic business facts
- `kb_policy` for evidence-backed narrative replies

---

## 7. Human-in-the-loop (HITL)

Low-confidence and high-risk cases must be human-reviewed because:
- security / legal mistakes are costly
- unsupported claims score zero in the challenge
- structured lookup gaps should not be patched by guesswork

Only reviewer-approved examples are appended to the `examples` index.
Structured facts and official policy documents remain curated sources outside the feedback loop.

---

## 8. Error handling (production essentials)

`wf_error_handler` performs three tasks:
1. Classify transient errors (timeouts, 429s) versus permanent failures
2. Retry transient errors with exponential backoff
3. Move permanent errors to a dead-letter queue and alert ops

This is especially important now that the system depends on multiple source types:
- structured lookup
- vector retrieval
- LLM classification / reply

---

## 9. Key files in this repository

- Main workflow: `workflows/wf_inbox_classifier.json`
- Human review: `workflows/wf_human_review_queue.json`
- Feedback to examples: `workflows/wf_feedback_to_rag.json`
- Error handler: `workflows/wf_error_handler.json`
- Confidence policy: `src/config/confidence_policy.json`
- Structured knowledge policy: `src/config/structured_knowledge.json`
- Vector index config: `src/config/vector_indexes.json`

---

## 10. Calibration and optimization (next steps)

1. Collect at least 100 human-reviewed examples
2. Measure:
   - category accuracy
   - escalation precision / recall
   - structured lookup coverage
   - document evidence sufficiency rate
3. Audit per-category source usage:
   - structured-only
   - structured + documents
   - escalate
4. Tune thresholds so the system prefers escalation over unsupported answers

---

## 11. One-line summary

This design keeps vector retrieval for classification and document fallback, but moves deterministic business knowledge toward structured lookup so the final agent is easier to audit, safer on unseen cases, and better aligned with the challenge scoring rules.
