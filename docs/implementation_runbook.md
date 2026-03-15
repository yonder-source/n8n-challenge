# Implementation Runbook

## 1) Data Preparation
- Source file: `data/test_dataset.csv`
- Command:
  - `python scripts/prepare_dataset.py`
  - `python scripts/build_embedding_requests.py`
- Output:
  - `data/test_dataset_canonical.csv`
  - `data/prepared_examples.jsonl`
  - `data/embedding_requests_examples.jsonl`

## 2) n8n Workflow Setup Order
1. `wf_error_handler`
2. `wf_human_review_queue`
3. `wf_feedback_to_rag`
4. `wf_inbox_classifier`
5. `wf_eval_runner`

## 3) Provider Integration
- Configure HTTP nodes for:
  - structured facts lookup endpoint
  - embedding model endpoint
  - tier1 and tier2 LLM endpoints
  - vector DB query/upsert endpoint
- `STRUCTURED_LOOKUP_URL` should implement the contract defined in `src/config/structured_knowledge.json`.
- Structured lookup is the first grounding source for pricing and security capability questions.
- Vector retrieval remains in use for:
  - `examples` similarity during classification
  - `kb_policy` document evidence when structured lookup is insufficient or policy wording matters

## 4) Evaluation
- Run `wf_eval_runner` against seed dataset.
- Track:
  - category accuracy
  - escalation precision
  - grounding pass rate
  - latency/cost per email

## 5) Human Feedback Loop
- Reviewer decisions are appended to `data/review_decisions.csv`.
- `wf_feedback_to_rag` ingests only approved records into the `examples` similarity index.
- Human review does not directly rewrite structured facts or policy documents; those should remain curated sources.

## 6) Error Operations
- Configure retry policy and dead-letter handling in `wf_error_handler`.
- Hook alerts to `ALERT_WEBHOOK_URL`.
