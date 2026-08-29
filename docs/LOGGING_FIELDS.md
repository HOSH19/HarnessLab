# HarnessLab Observability Field Inventory & Reduction

This document inventories every field logged or traced across the HarnessLab observability stack, recommends a **top-5 minimal set** for A/B harness experiments, and records what was removed.

**Guiding question:** *Did harness X beat harness Y on task Z, and why?*

---

## Full field inventory (pre-reduction)

### Trace metadata (`_invoke_config` → LangGraph `configurable`)

| Field | Source | Purpose |
|---|---|---|
| `thread_id` | `runner._invoke_config` | LangGraph checkpoint key; required by `extract_langgraph_trajectory_from_thread` |
| `harness_name` | `harness.name` | Identifies A/B arm |
| `harness_version` | YAML `observability.trace_metadata` | Static version tag (`"1.0"` in all example harnesses) |
| `model` | `HARNESSLAB_MODEL` / `--by models` | Model arm for model comparisons |
| `flaky_tools` | Task `inputs.flaky_tools` | Copied into trace config during invoke |

### Run outputs (`_extract_outputs` → LangSmith/Langfuse run `outputs`)

| Field | Purpose |
|---|---|
| `output` | LangSmith Outputs column display text (duplicate of `classification`) |
| `classification` | Parsed triage category from `classify` tool |
| `details.final_reply` | Draft reply from `draft_reply` tool |
| `details.tool_names` | Ordered tool invocation names |
| `details.error_count` | Tool errors accumulated in graph state |
| `details.graph_trajectory` | Full LangGraph trajectory (`steps`, `results`, `inputs`) |
| `error` | Exception string when graph invoke fails |

### Experiment metadata (`run_experiment` → `evaluate(metadata=…)`)

| Field | Purpose |
|---|---|
| `harness` | Full `HarnessConfig` Pydantic dump (execution, tooling, context, observability) |
| `model` | Model name when running a model-comparison arm |

### Evaluator feedback keys (8)

| Key | Reads from run | Compares to dataset |
|---|---|---|
| `task_pass` | `classification`, `final_reply` | `expected_category`, `required_reply_terms` |
| `graph_trajectory` | `graph_trajectory` | `expected_nodes` |
| `tool_sequence` | `tool_names` or `graph_trajectory` | `expected_tools` |
| `error_recovery` | `error_count` | `max_acceptable_errors` |
| `step_count` | child runs + `graph_trajectory` | `expected_max_steps` |
| `efficiency` | run latency/tokens + `graph_trajectory` | `expected_max_steps` |
| `failure_fingerprint` | `classification`, `final_reply`, `run.error`, latency | — |
| `reply_text` | `final_reply` | — (human-readable column) |

Evaluators are **not** trace payload fields; they are derived scores stored as experiment feedback. No change recommended.

### Task dataset fields (LangSmith Examples)

**Inputs:** `prompt`, `ticket_id`, `flaky_tools`, `conversation_history`

**Reference outputs:** `expected_category`, `required_reply_terms`, `reply_hint`, `expected_nodes`, `expected_tools`, `expected_max_steps`, `max_acceptable_errors`, `stress`

Dataset fields define *what good looks like* per task. They should remain on the example, not be duplicated into trace tags.

### Local JSON persistence (`store.serialize_result_row`)

| Field | Purpose |
|---|---|
| `example_id` | Dataset row identity |
| `run_id` | Trace identity |
| `inputs` | Copy of example inputs |
| `outputs` | Copy of run outputs |
| `evaluation_results` | All evaluator scores/comments |

Local persistence is a full experiment archive; it mirrors whatever the runner emits in `outputs`.

---

## Top 5 fields to keep

These five fields are the minimum needed to answer win/loss and root-cause questions in harness A/B runs.

| # | Field | Layer | Why it matters for A/B debugging |
|---|---|---|---|
| 1 | **`harness_name`** | Trace tag | Groups traces and scores by variant (`minimal` vs `retry` vs `trim`). Without it you cannot attribute a run to an experiment arm. |
| 2 | **`classification`** | Run output | Primary correctness signal — did the agent pick the right triage category? Drives `task_pass` and the LangSmith Outputs column vs `expected_category`. |
| 3 | **`graph_trajectory`** | Run output | Explains *why* one harness won: different node paths (trim middleware), extra agent↔tools loops (retries), skipped steps. Powers `graph_trajectory`, `tool_sequence`, `step_count`, and `efficiency` evaluators. |
| 4 | **`final_reply`** | Run output | Second correctness axis — required reply terms (`database`, `timeout`, etc.). Separates “right category, bad reply” partial failures that category alone would miss. |
| 5 | **`error_count`** | Run output | Stress-task differentiator — flaky-tool scenarios (`T-011`, `T-015`) are where retry harnesses should win. Directly feeds `error_recovery` and explains recovery vs give-up behavior. |

### Operational fields kept but not counted in the top 5

| Field | Reason kept |
|---|---|
| `thread_id` | Required internally for trajectory extraction; not promoted as a Langfuse/LangSmith filter tag |
| `error` | Only on invoke failure; essential for diagnosing crashes without a full trajectory |

---

## Fields removed (safe to drop)

| Field | Layer | Why removable |
|---|---|---|
| `harness_version` | Trace metadata | Static `"1.0"` on all example harnesses; adds no A/B discrimination |
| `model` | Trace metadata | Already on experiment metadata and `experiment_prefix` for model compares |
| `flaky_tools` | Trace metadata | Duplicates `example.inputs.flaky_tools` on every stress task |
| `output` | Run output | Exact duplicate of `classification` for display |
| `tool_names` | Run output | Derivable from `graph_trajectory` via `extract_tool_names_from_trajectory` |
| `details` wrapper | Run output | Unnecessary nesting; top-level fields work with `run_output_field` helper |
| YAML `trace_metadata.harness_version` | Harness config | Removed from all three example harness YAMLs |

### Fields retained elsewhere (not duplicated in traces)

| Field | Where it lives instead |
|---|---|
| Full harness config | Experiment `metadata.harness` (unchanged — useful for experiment-level audit, not per-span payload) |
| Model name | Experiment `metadata.model` + experiment name prefix |
| Task inputs / references | LangSmith dataset example `inputs` / `outputs` |
| Evaluator scores | Experiment feedback columns (`task_pass`, etc.) |
| Local archive | `.harnesslab/runs/` JSON bundles |

---

## Implementation status

**Status:** implemented on `main`.

### Code changes

1. **`harnesslab/config/models.py`** — `ObservabilityConfig.trace_metadata` defaults to `{}` with documentation that `harness_name` is injected by the runner; avoid duplicating dataset fields.

2. **`harnesslab/experiments/runner.py`**
   - `_invoke_config`: emits only `thread_id` (internal) + `harness_name` (+ optional user `trace_metadata`); no longer tags `model` or `flaky_tools`.
   - `_extract_outputs` / `_empty_outputs`: flat dict with `classification`, `final_reply`, `graph_trajectory`, `error_count` only.

3. **`examples/ticket_triage/harnesses/*.yaml`** — removed static `trace_metadata.harness_version` blocks.

### Evaluator compatibility

All eight evaluators continue to work:

- `run_output_field` reads top-level or legacy `details.*` keys.
- `extract_tool_names_from_outputs` falls back to `graph_trajectory` when `tool_names` is absent.

---

## Quick reference: before vs after

```
BEFORE trace tags:     thread_id, harness_name, harness_version, model, flaky_tools
AFTER trace tags:      thread_id (internal), harness_name

BEFORE run outputs:    output, classification, details.{final_reply, tool_names, error_count, graph_trajectory}
AFTER run outputs:     classification, final_reply, graph_trajectory, error_count
```

**Payload reduction:** 9 logged fields → 5 (plus internal `thread_id` and failure-only `error`).
