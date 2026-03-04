# n8n Inbox Inferno (Nexus Integrations AI Evals)

This repo contains a production-minded starter for the challenge:
- email classifier workflow
- confidence-gated escalation
- RAG with leakage-safe indexing
- human-in-the-loop feedback loop
- evaluation runner

## Structure
- `workflows/`: n8n workflow blueprints
- `src/config/`: routing, confidence, vector index configs
- `src/mappings/`: taxonomy, actions, data cleaning, RAG schema
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

## Detailed Design
- English (beginner-friendly) architecture and formula rationale: [docs/email_classifier_full_design_en.md](docs/email_classifier_full_design_en.md)
 

## Quick Local Test
Run the data preparation scripts to validate the pipeline locally:

```powershell
# (activate your Python environment first)
python scripts/prepare_dataset.py
python scripts/build_embedding_requests.py
```

If you want to run the workflows without real API keys, consider configuring mock endpoints for `EMBEDDING_URL`, `VECTOR_SEARCH_URL`, and `LLM_CLASSIFIER_URL` and set them in `src/config/.env.example` or your environment.
