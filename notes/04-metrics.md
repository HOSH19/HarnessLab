# Experiment metrics (what each column means)

LangSmith experiment tables mix **HarnessLab feedback** (our evaluators) with **built-in trace columns**. Only the five keys below are published today via `EVALUATORS` in `harnesslab/experiments/runner.py`.

Dropped from publishing (modules may still exist under `harnesslab/eval/`): `efficiency`, `failure_fingerprint`, `run_cost_usd`, `cost_efficiency`. Older experiments can still show those keys forever.

Product detail: [docs/EVALUATORS.md](../docs/EVALUATORS.md).

---

## A) Published HarnessLab feedback

| Key | Range | Reads from run | Compares to example | What “good” means |
|---|---|---|---|---|
| `task_pass` | 0.0–1.0 | `classification`, `details.final_reply` | `classification`, `required_reply_terms` | Correct category + required reply terms |
| `graph_trajectory` | 0.0–1.0 | `details.graph_trajectory` | `expected_nodes` | Expected nodes appear in order (subsequence) |
| `coordination_pass` | 0.0–1.0 | `details.graph_trajectory` | `required_stages` (else `expected_nodes`) | Required stages appear in order |
| `error_recovery` | 0.0–1.0 | `error_count` | `max_acceptable_errors` (default 0) | Tool errors stay within budget |
| `ttft_seconds` | seconds | `details.ttft_seconds` (else run timing / `new_token`) | — | Lower wall-clock time to first token |

### Scoring (from code, not folklore)

**`task_pass`** — 50% category match (`expected classification` substring in run classification) + 50% fraction of `required_reply_terms` found in the reply. Empty expectations count as satisfied for that half.

**`graph_trajectory`** — `subsequence_progress(expected_nodes, actual_nodes)`. Full credit when the expected list is a subsequence of visited nodes; partial credit for a matching prefix. **Skipped → 1.0** when the task has no `expected_nodes`.

**`coordination_pass`** — Same progress metric on `required_stages` (preferred) or `expected_nodes`. **Skipped → 1.0** when neither is set. Use this for multi-node topologies (pipeline / supervisor / plan-execute).

**`error_recovery`** — `1.0` if `error_count <= max_acceptable_errors`; otherwise `max(0.0, 1.0 - 0.25 * excess)`. Gate treats this (with `task_pass`) as blocking.

**`ttft_seconds`** — Wall-clock seconds (lower is better). Prefers `details.ttft_seconds` measured during the Target run; falls back to `first_token_time` / root `new_token` events. Missing timing → score `0.0` with comment `ttft_unavailable`.

### Why these five

| Key | Why it matters in A/B |
|---|---|
| `task_pass` | Primary win/loss: wrong category or missing reply terms should lose |
| `graph_trajectory` | Explains *path* differences (retry loops, trim, topology) |
| `coordination_pass` | Did the multi-node graph hit required stages? |
| `error_recovery` | Flaky-tool stress (`R-001`, …): retry harness should beat minimal |
| `ttft_seconds` | Visible TTFT cell when LangSmith’s native column is blank |

---

## B) LangSmith built-in columns (not our evaluators)

These appear because traces have timing/usage metadata. We do **not** control them via `EVALUATORS`. Hide unused columns in the LangSmith UI if the table feels crowded.

| Column | Meaning |
|---|---|
| **Latency** | End-to-end run duration from the trace |
| **Time to First Token** | Native TTFT from the platform — often **blank** for agent `evaluate` Targets even when streaming worked. Prefer feedback **`ttft_seconds`** |
| **Total / Input / Output Tokens** | Token usage attached to the run (when the provider reports it) |
| **Total / Input / Output Cost** | Cost estimate LangSmith derives from usage + pricing |

---

## Practical reading tip

Open the **newest** experiment after a compare. Read our five feedback keys first; treat native TTFT as optional noise; use token/cost columns only when you care about spend, knowing Pareto HTML may estimate cost locally without publishing `run_cost_usd`.
