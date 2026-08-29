# Logged output fields

HarnessLab attaches a **minimal set of five fields** to each run for A/B debugging. Evaluator definitions live in [EVALUATORS.md](EVALUATORS.md).

**Guiding question:** *Did harness X beat harness Y on task Z, and why?*

## Trace tag

| Field | Purpose |
|---|---|
| `harness_name` | Groups runs by A/B arm (`minimal`, `retry`, `trim`) |

`thread_id` is set internally for trajectory extraction but is not promoted as a filter tag.

## Run outputs

| Field | Purpose |
|---|---|
| `classification` | Parsed triage category — primary correctness signal |
| `final_reply` | Draft reply text — required-term checks |
| `graph_trajectory` | LangGraph node path — explains behavioral differences |
| `error_count` | Tool errors accumulated — stress-task retry differentiator |

`error` is included only when graph invocation fails.

## Experiment metadata

Full harness config and model name live on experiment metadata (not duplicated per-span).

## Dataset fields

Task **inputs** (`prompt`, `ticket_id`, `flaky_tools`, `conversation_history`) and **reference outputs** (`expected_category`, `expected_nodes`, etc.) stay on LangSmith examples — not copied into trace tags.

## Local persistence

`.harnesslab/runs/` JSON mirrors run outputs and evaluator scores for offline review.
