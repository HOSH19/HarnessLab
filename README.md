# HarnessLab

[![CI](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml/badge.svg)](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml)

A/B test **agent harnesses** (retries, context trim, turn limits) and **models** on the same LangGraph ticket-triage agent. Declare variants in YAML, run stress tasks, score with LangSmith evaluators, compare in an HTML report.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [docs/DEMO.md](docs/DEMO.md) for more detail.

## How it works

```mermaid
flowchart LR
    YAML[harnesses/*.yaml] --> Builder[graph builder]
    Graph[LangGraph agent] --> Builder
    Builder --> Run[invoke per task]
    Run --> LS[LangSmith traces]
    LS --> Eval[evaluators]
    Eval --> Report[HTML report]
```

Harness YAML → compiled LangGraph agent → LangSmith `evaluate()` per task → seven custom evaluators → `report.html` plus local JSON under `.harnesslab/runs/`.

**Harness variants:** `minimal` (no middleware), `retry` (tool retries), `trim` (message history cap).

**Stress suite:** 6 tasks (T-011–T-016) — flaky tools, long history, ambiguous tickets, multi-search, SLA escalation.

Agent policy lives in `examples/ticket_triage/rules.py` (read → KB search → classify → reply; optional `check_sla` / `escalate_ticket` for SLA/outage tickets).

## LangSmith dashboard

Without `--local`, traces and scores live in LangSmith (project `triage`, dataset `ticket-triage-stress`). A local `report.html` is also written.

Three harness experiments on 6 stress tasks:

![LangSmith experiment comparison across three harness variants](docs/images/langsmith-dashboard.png)

| Area | What you see |
|---|---|
| **Experiments** | One row per harness (`minimal`, `retry`, `trim`), 6/6 completed |
| **Feedback** | `efficiency` and `error_recovery` at 1.0 for all three; `failure_fingerprint` ~0.67 |
| **Latency** | `minimal` slowest (P50 ~9s); `retry` and `trim` faster (~4–5s P50) |
| **Tokens** | `minimal` uses far more input tokens than `retry` / `trim` |

Aggregate charts look even — drill into per-task rows for real differences.

### Per-task scores

![LangSmith per-task evaluator scores for one experiment](docs/images/langsmith-per-task.png)

In this `trim` run, `task_pass` averages **0.50** and `tool_sequence` **0.00** while `efficiency` / `error_recovery` stay at 1.0:

- **1.0 on efficiency / error_recovery** — run finished without crashing, not "got the right answer"
- **Below 1.0 on task_pass / tool_sequence** — wrong category, missing reply terms, or skipped tools
- Compare the same view across `minimal`, `retry`, and `trim` to see harness impact

### Agent loop trace

![LangSmith trace view showing the agent loop for a single task run](docs/images/langsmith-trace.png)

Trace for ticket **T-015** under the `trim` harness: `trim_context` → `agent` → `tools` (`read_ticket`, `search_kb`, `classify`, `draft_reply`) with flaky `search_kb` retries. The right panel shows evaluator scores and structured output (`classification`, `final_reply`, `graph_trajectory`).

## Compare modes

Both modes run the **same stress tasks** (2 by default, or filter with `--task` / `--tasks`).

| `--by` | What varies | What stays fixed | Default run |
|---|---|---|---|
| **`harness`** | Harness YAML (`minimal`, `retry`) | Model from `HARNESSLAB_MODEL` | 2 harnesses × 2 tasks |
| **`models`** | Cheap models (`nano`, `mini`, `turbo`) | Single `--harness` (default `minimal`) | 3 models × 2 tasks |

Default model compare arms: `gpt-4.1-nano`, `gpt-4.1-mini`, `gpt-3.5-turbo`. Override with `--models nano,mini`.

Full stress suite (6 tasks, all harnesses):

```bash
harnesslab compare examples/ticket_triage --harness minimal,retry,trim --tasks 6 -o report.html
```

```bash
cd harnesslab
conda env create -f environment.yml && conda activate harnesslab
cp .env.example .env   # set OPENAI_API_KEY, LANGSMITH_API_KEY

# Harness compare (local) — default 2 harnesses × 2 tasks
harnesslab compare examples/ticket_triage --local -o report.html

# LangSmith upload (same default)
harnesslab compare examples/ticket_triage -o report.html

# Cheapest LangSmith upload (1 harness × 1 task)
harnesslab compare examples/ticket_triage --task T-011 -o report.html

# Model compare
harnesslab compare examples/ticket_triage --by models --local

pytest -q
```

## Environment

| Variable | Required | Default |
|---|---|---|
| `OPENAI_API_KEY` | yes | — |
| `LANGSMITH_API_KEY` | yes (unless `--local`) | — |
| `LANGSMITH_ENDPOINT` | non-US accounts | `https://api.smith.langchain.com` |
| `HARNESSLAB_MODEL` | no | `gpt-4.1-nano` |

APAC users: `LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com`. GitHub Actions needs `OPENAI_API_KEY` as a repo secret.

## Saving LangSmith traces

LangSmith counts **every span** (each `agent`, `tools`, and `ChatOpenAI` node), not just top-level experiment rows. A full harness compare (3 harnesses × 6 tasks) can use **100–200+ traces**.

| Goal | Command | Approx. top-level runs |
|---|---|---|
| Dev / free | `--local` | 0 LangSmith traces |
| Cheapest upload | `--task T-011` | 2 experiments × 1 task |
| Default upload | (no flags) | 2 harnesses × 2 tasks |
| Full stress suite | `--harness minimal,retry,trim --tasks 6` | 3 harnesses × 6 tasks |

Use `--local` while iterating; upload with the default compare or `--task` when you need the LangSmith dashboard.

## License

MIT
