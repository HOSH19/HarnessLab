# HarnessLab

[![CI](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml/badge.svg)](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml)

A/B test **agent harnesses** (retries, context trim, turn limits) and **models** on the same LangGraph ticket-triage agent. Declare variants in YAML, run stress tasks, score with Langfuse evaluators, compare in an HTML report.

## How it works

Harness YAML → compiled LangGraph agent → Langfuse `run_experiment()` per task → seven custom evaluators → `report.html` plus local JSON under `.harnesslab/runs/`.

**Harness variants:** `minimal`, `retry`, `trim`

**Stress suite:** 6 tasks (T-011–T-016)

## Quick start

```bash
cd harnesslab
conda env create -f environment.yml && conda activate harnesslab
pip install -e ".[dev]"
cp .env.example .env   # OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

# Harness compare (local — no Langfuse upload)
harnesslab compare examples/ticket_triage --local -o report.html

# Langfuse upload + dataset experiment comparison
harnesslab compare examples/ticket_triage -o report.html

# Model compare
harnesslab compare examples/ticket_triage --by models --local

pytest -q
```

## Compare modes

| `--by` | Varies | Fixed |
|---|---|---|
| **`harness`** (default) | `minimal`, `retry`, `trim` | Model (`HARNESSLAB_MODEL` in `.env`) |
| **`models`** | `nano`, `mini`, `turbo` | Harness (`--harness minimal`) |

## Environment

| Variable | Required | Default |
|---|---|---|
| `OPENAI_API_KEY` | yes | — |
| `LANGFUSE_PUBLIC_KEY` | yes (unless `--local`) | — |
| `LANGFUSE_SECRET_KEY` | yes (unless `--local`) | — |
| `LANGFUSE_BASE_URL` | no | `https://cloud.langfuse.com` |
| `HARNESSLAB_MODEL` | no | `gpt-4.1-nano` |

Use `--local` to skip Langfuse uploads during development. View experiment comparisons in the Langfuse UI under **Datasets → ticket-triage-stress**.

## License

MIT
