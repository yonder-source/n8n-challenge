# n8n Inbox Inferno (Nexus Integrations AI Evals)

This repo contains a production-minded starter for the challenge:
- email classifier workflow
- confidence-gated escalation
- structured-first grounding with leakage-safe retrieval
- human-in-the-loop feedback loop
- evaluation runner

## Structure
- `workflows/`: n8n workflow blueprints
- `src/config/`: routing, confidence, structured knowledge, vector index configs
- `src/mappings/`: taxonomy, actions, data cleaning, retrieval schema
- `src/prompts/`: classifier/reply prompts
- `data/`: source dataset and prepared artifacts
- `scripts/`: data prep and embedding request builders
- `eval/`: run logs and metrics outputs
- `docs/`: strategy and runbook

## Quick Start
1. Fill secrets from `src/config/.env.example`.
2. Run data prep:
   - `python scripts/prepare_dataset.py`
   - `python scripts/build_embedding_requests.py`
3. Build/import workflows under `workflows/` in n8n.
4. Configure provider HTTP credentials in n8n.
5. Start with `wf_eval_runner` to baseline metrics.

## Important Guardrail
Do not place `expected_category` or `expected_action` into retrievable inference index content.
Use them only for evaluation and supervised learning artifacts.

For this challenge, prefer structured facts for deterministic business data such as pricing, capability matrices, and routing policy.
Use vector retrieval for:
- example similarity during classification
- official document evidence when structured facts are missing or insufficient

## Detailed Design
- English (beginner-friendly) architecture and formula rationale: [docs/email_classifier_full_design_en.md](docs/email_classifier_full_design_en.md)
 

## Quick Local Test
Run the data preparation scripts to validate the pipeline locally:

```powershell
# (activate your Python environment first)
python scripts/prepare_dataset.py
python scripts/build_embedding_requests.py
```

If you want to run the workflows without real API keys, consider configuring mock endpoints for `STRUCTURED_LOOKUP_URL`, `EMBEDDING_URL`, `VECTOR_SEARCH_URL`, `LLM_CLASSIFIER_URL`, and `LLM_REPLY_URL` and set them in `src/config/.env.example` or your environment.
