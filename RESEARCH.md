a# Prompt2Cal — Research reproduction guide

This document is for **capstone markers, supervisors, and researchers** who need to understand or reproduce the benchmark evaluation reported in the final report. The product-facing guide remains in [README.md](README.md).

## Overview

| Category | Description |
| --- | --- |
| `clean` | Well-formed, unambiguous scheduling phrases |
| `typos` | Common spelling / transcription errors |
| `voice_to_text` | ASR-style fragments and disfluencies |
| `ambiguous` | Vague or approximate times (e.g. “around 7ish”) |
| `missing_fields` | Deliberately incomplete inputs (location only, no time, etc.) |

Ground truth, labelling rules, and supervisor notes live under `benchmark/`:

- `benchmark/dataset.json` — frozen benchmark (rebuild from catalog via `scripts/build_benchmark_dataset.py`)
- `benchmark/labelling_notes.md` — non-obvious labelling decisions
- `benchmark/README.md` — category targets and labelling conventions

The evaluation harness scores **accuracy (F1)**, **robustness** (clean vs perturbed drop), **consistency** (pairwise agreement across repeated LLM runs), and **hallucination rate** (fabricated non-null fields when ground truth is null). Statistical tests (McNemar, Wilcoxon) are computed inside the runner summary.

The **source-grounding verifier** (`backend/evaluation/verifier.py`) is scored separately and also powers live **confidence highlighting** in the Chrome extension (`backend/services/confidence.py`).

---

## Prerequisites

From the repository root:

```bash
pip install -r requirements.txt
cp env.example .env
```

### Environment variables

| Variable | Required for | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | GPT benchmark runs | Used when `--provider openai` |
| `ANTHROPIC_API_KEY` | Claude benchmark runs | Used when `--provider claude` |
| `LLM_PROVIDER` | Live backend only | Production parser default (`claude`) |
| `LLM_MODEL` | Live backend only | e.g. `claude-sonnet-4-6` |

Calendar OAuth keys (`GOOGLE_*`, `MS_*`) are **not** required for benchmark reproduction — the harness only calls extractors, not Google/Microsoft APIs.

All evaluation runs use the dataset timezone **`Australia/Sydney`** (stored in `benchmark/dataset.json`).

---

## Single command: full benchmark re-run

Section 3.5 (*Evaluation procedure*) of the final report states that the full benchmark can be re-executed from one documented command. From the repository root:

### Claude Sonnet 4.6 (live product model)

```bash
python scripts/run_evaluation.py \
  --provider claude \
  --model claude-sonnet-4-6 \
  --output-dir benchmark/outputs_claude \
  --llm-runs 3 \
  --temperature 0.0
```

### GPT-5 (research comparison model)

```bash
python scripts/run_evaluation.py \
  --provider openai \
  --model gpt-5 \
  --output-dir benchmark/outputs \
  --llm-runs 3 \
  --temperature 0.0
```

> **API cost warning:** Each full run executes the LLM extractor **3 times × 100 inputs = 300 API calls**, plus one Regex pass per input (local, no API). Re-running both extractors therefore consumes paid OpenAI and Anthropic quota. Use `--input-id` (repeatable) for smoke tests on a single input before committing to a full run.

### Regex only (no API calls)

Deterministic baseline; useful for verifying the harness without spending credits:

```bash
python scripts/run_evaluation.py --regex-only --output-dir benchmark/outputs
```

### Smoke test (one input)

```bash
python scripts/run_evaluation.py \
  --provider claude \
  --model claude-sonnet-4-6 \
  --output-dir benchmark/outputs_smoke \
  --input-id clean_01 \
  --llm-runs 1
```

### All `run_evaluation.py` flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `--dataset` | `benchmark/dataset.json` | Benchmark file path |
| `--output-dir` | `benchmark/outputs` | Per-input JSON + `summary.json` |
| `--input-id` | (all inputs) | Restrict to specific IDs; repeatable |
| `--llm-runs` | `3` | Repeated LLM extractions per input |
| `--temperature` | `0.0` | LLM sampling temperature |
| `--regex-only` | off | Skip LLM calls entirely |
| `--provider` | `openai` | `openai` or `claude` |
| `--model` | provider default | Override model name |

On completion, headline metrics are printed to stdout and written to `{output-dir}/summary.json`. Each input also gets `{output-dir}/{input_id}.json` containing raw Regex output, all LLM runs, ground truth, and per-input metrics.

**Note:** OpenAI’s GPT-5 endpoint rejects `temperature=0`; the harness omits the parameter and uses the model default (documented in `benchmark/labelling_notes.md`).

---

## Verification from stored artefacts (no API calls)

These scripts read the JSON artefacts produced by `run_evaluation.py`. They recompute every reported verification figure without re-calling any LLM.

### Source-grounding verifier scoring

Scores whether predicted fields are **grounded in the source text** vs **fabricated** (ground truth null). Writes `benchmark/verifier_results.json`.

```bash
python scripts/run_verifier.py
```

Custom extractor directories:

```bash
python scripts/run_verifier.py \
  --extractor gpt-5 benchmark/outputs \
  --extractor claude-sonnet-4-6 benchmark/outputs_claude \
  --output benchmark/verifier_results.json
```

Implementation: `backend/evaluation/verifier.py` · Unit tests: `backend/tests/test_verifier.py`

### Sensitivity analysis (alignment threshold)

Recomputes mean F1 at alignment thresholds **0.6, 0.7, 0.8** (main analysis uses 0.7). Writes `benchmark/sensitivity_results.json`.

```bash
python scripts/run_sensitivity.py
```

### Failure-mode taxonomy

Counts deviation types (empty output, missed/spurious events, fabricated/missed/wrong fields). Writes `benchmark/failure_taxonomy.json`.

```bash
python scripts/build_failure_taxonomy.py
```

### Reproducibility check

Compares a fresh re-run against stored artefacts (Regex byte-identical; Claude summary deltas):

```bash
# After re-running regex-only into benchmark/outputs_regex_rerun
# and Claude into benchmark/outputs_claude_rerun:
python scripts/check_reproducibility.py
```

---

## Where outputs land

| Path | Contents |
| --- | --- |
| `benchmark/dataset.json` | 100 inputs + ground truth |
| `benchmark/outputs/` | GPT-5 run artefacts + `summary.json` |
| `benchmark/outputs_claude/` | Claude Sonnet 4.6 artefacts + `summary.json` |
| `benchmark/verifier_results.json` | Verifier confusion matrices |
| `benchmark/sensitivity_results.json` | Threshold sensitivity table |
| `benchmark/failure_taxonomy.json` | Failure-mode counts per extractor |
| `benchmark/APPENDIX_dataset.md` | Human-readable dataset appendix |
| `benchmark/APPENDIX_dataset.tex` | LaTeX appendix table |

Regenerate appendix tables from the dataset:

```bash
python scripts/build_appendix_table.py
python scripts/build_benchmark_dataset.py   # rebuild dataset.json from inputs_catalog.py
```

---

## Harness source layout

| Component | Location |
| --- | --- |
| Dataset models & loader | `backend/evaluation/models.py` |
| Normalisation & date parsing | `backend/evaluation/normalize.py` |
| Event alignment | `backend/evaluation/alignment.py` |
| Metrics (F1, hallucination, consistency, tests) | `backend/evaluation/metrics.py` |
| Evaluation runner | `backend/evaluation/runner.py` |
| Regex / LLM extractors | `backend/evaluation/extractors.py` |
| CLI entry point | `scripts/run_evaluation.py` |
| Unit tests | `backend/tests/test_verifier.py`, `backend/tests/test_confidence.py`, metric tests alongside harness |

Run harness-related unit tests:

```bash
python -m pytest backend/tests/test_verifier.py backend/tests/test_confidence.py -q
```

---

## From research to product

Findings from the verifier were integrated into the live Chrome extension:

- **`backend/services/confidence.py`** — per-field `field_confidence` (`grounded` / `ungrounded` / `corroborated`) attached to parsed events
- **Confirm UI** — fields not found in the user’s text are highlighted before creation
- **`end_time_assumed`** — end times inferred from default duration (not from an explicit range or stated duration) are labelled separately in the UI

The live parser uses **Claude Sonnet 4.6** (`LLM_PROVIDER=claude`). The research harness can still target OpenAI or Claude independently for controlled comparison.

---

## Further reading

- Final report (methodology & results): [`report/FINAL_REPORT.md`](report/FINAL_REPORT.md) *(included in the archive)*
- Report figures (regenerate charts and diagrams): [`report/figures/README.md`](report/figures/README.md)
- Benchmark labelling: `benchmark/README.md`, `benchmark/labelling_notes.md`
- Product setup & extension install: [README.md](README.md)
