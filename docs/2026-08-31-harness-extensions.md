# Harness extensions worklog (2026-08-31)

Session notes for [PR #12](https://github.com/HOSH19/HarnessLab/pull/12) — middleware, cost evaluators, regression gate, and local-run fixes.

---

## Summary

HarnessLab gained five new harness presets (`cache`, `circuit_breaker`), two cost evaluators (`run_cost_usd`, `cost_efficiency`), and a local regression gate (`benchmark` + `gate`). Local runs now track real token usage and cost, CLI warnings were fixed at the source, and gate output was trimmed with an optional `--verbose` mode.

---

## 1. Middleware: cache and circuit breaker

**Goal:** Extend harness engineering without new agents — add reusable tool middleware.

**Added modules** (`harnesslab/middleware/`):

| Module | Role |
|---|---|
| `runtime.py` | Per-run context for cache and circuit-breaker state |
| `cache.py` | Memoize idempotent read tools within a run |
| `wrap.py` | Apply middleware around individual tool calls |
| `tools.py` | `prepare_tools()`, `make_tools_node()` |

**Config** (`ToolingConfig` in `harnesslab/config/models.py`):

- `cache_reads: bool` — enable read-tool memoization
- `circuit_breaker_threshold: int | null` — open circuit after N consecutive tool failures

**YAML presets** (both examples):

- `examples/incident_manager/harnesses/cache.yaml`
- `examples/incident_manager/harnesses/circuit_breaker.yaml`
- `examples/research_agent/harnesses/cache.yaml`
- `examples/research_agent/harnesses/circuit_breaker.yaml`

---

## 2. Cost evaluators

**Goal:** Score runs on dollar cost and value-for-money in LangSmith and local reports.

**Added:**

- `harnesslab/eval/cost.py` — `estimate_run_cost_usd()`, `resolve_run_model()`
- `harnesslab/eval/cost_evaluators.py` — `run_cost_usd`, `cost_efficiency`
- `harnesslab/config/model_catalog.py` — `MODEL_COST_PER_1K_TOKENS` pricing table

**Registered** in `harnesslab/experiments/runner.py` alongside the original five evaluators (seven total). See [EVALUATORS.md](EVALUATORS.md).

---

## 3. Regression gate (`benchmark` + `gate`)

**Goal:** Catch score regressions in CI without LangSmith uploads on every PR.

**Added:**

- `harnesslab/gate/baseline.py` — load/save/compare baseline JSON
- `harnesslab/gate/significance.py` — bootstrap mean delta + 95% CI
- `harnesslab/gate/check.py` — pass/fail on blocking evaluators
- `harnesslab/cli/gate_cli.py` — CLI commands

**Blocking evaluators:** `task_pass`, `error_recovery` (default `--max-regression 0.05`).

**Docs:** [GATE.md](GATE.md)

### Gate output behavior

By default, gate prints only:

- Blocking evaluators (`task_pass`, `error_recovery`) — always shown
- Non-blocking evaluators — only when delta or CI is non-zero

Use `--verbose` / `-v` to print every evaluator row for every arm.

**Why many rows show `delta=0.0`:** When baseline and gate use the same tasks and harnesses, deterministic evaluators (`graph_trajectory`, `error_recovery`, `failure_fingerprint`) often score identically on every task. Bootstrap then returns `delta=0.0, ci=[0.0, 0.0]`. Only `task_pass` (LLM non-determinism) and cost metrics typically move between back-to-back runs.

---

## 4. Local token and cost tracking fix

**Problem:** In `--local` mode, LangSmith does not populate `run.total_tokens` on Run objects, so `run_cost_usd` was always `0` and `cost_efficiency` was inflated (dividing by `1e-6`).

**Fix:**

1. During `graph.invoke()`, wrap with LangChain `get_usage_metadata_callback()` and attach `total_tokens`, `model`, and `usage_metadata` to target outputs (`harnesslab/experiments/target.py`).
2. Extend `run_total_tokens()` to read from `run.outputs` and child runs (`harnesslab/eval/run_metrics.py`).
3. Add shared helpers in `harnesslab/eval/token_usage.py`.

**Important:** Re-export baselines after this fix. Old baseline JSON with `run_cost_usd: 0.0` will produce misleading `cost_efficiency` deltas until replaced.

---

## 5. Local experiment runner (warning fix)

**Problem:** `langsmith.evaluate(..., upload_results=False)` emitted `LangSmithBetaWarning` on every local benchmark/gate run.

**Fix:** Added `harnesslab/experiments/local_runner.py` — runs target + evaluators in-process without calling the beta upload path. `run_experiment()` uses this when `upload_results=False`.

---

## 6. LangGraph `RunnableConfig` typing fix

**Problem:** `UserWarning` on `graph.add_node("tools", ...)` — LangGraph only recognizes `Optional[RunnableConfig]`, not `RunnableConfig | None` (PEP 604 union).

**Fix:** Updated tool node signatures in `middleware/tools.py`, `middleware/retry.py`, and `examples/agent_nodes.py`.

---

## 7. Code quality and docs

- Split CLI into `compare_runner.py`, `gate_cli.py`; shortened `main.py`
- Pareto cost chart in `harnesslab/report/pareto.py`
- README condensed to three sections; added [GATE.md](GATE.md)
- **100 tests** passing at end of session

---

## Commands reference

### Full local baseline + gate (all evaluators in terminal)

```bash
# 1. Export baseline (full JSON with all 7 evaluators per task)
python3 -m harnesslab benchmark examples/incident_manager \
  --harness minimal,retry --tasks 6 --local -o /tmp/baseline.json

# 2. View full JSON
python3 -m json.tool /tmp/baseline.json

# 3. Gate with every evaluator row
python3 -m harnesslab gate examples/incident_manager \
  --baseline /tmp/baseline.json --harness minimal,retry --tasks 6 --local --verbose
```

### LangSmith — one harness, new cost evals

Requires `OPENAI_API_KEY` and `LANGSMITH_API_KEY` in `.env`. Do not pass `--local`.

```bash
# Incident manager → LangSmith project: incident-manager
python3 -m harnesslab run examples/incident_manager --harness cache --tasks 6

# Research agent → LangSmith project: research-agent
python3 -m harnesslab run examples/research_agent --harness cache --tasks 4
```

### Compare with HTML report + Pareto chart (LangSmith upload)

```bash
python3 -m harnesslab compare examples/incident_manager \
  --harness cache,circuit_breaker --tasks 6 -o incident-report.html
```

### New harness presets on research agent (local)

```bash
python3 -m harnesslab compare examples/research_agent \
  --harness cache,circuit_breaker --tasks 4 --local -o research-report.html
```

---

## Pitfalls we hit (and fixes)

| Issue | Cause | Fix |
|---|---|---|
| LangSmith traces missing | Used `--local` (disables upload/tracing) | Drop `--local` or use `--no-local` explicitly for upload mode |
| Gate `cost_efficiency` delta in six figures | Baseline created before cost fix (`run_cost_usd: 0`) | Re-run `benchmark` after pulling cost-tracking fix |
| Gate `task_pass` delta ~0.14 | `--tasks 6` baseline vs `--task I-101` gate | Match `--tasks` / `--task` flags between benchmark and gate |
| Gate many `0.0` rows | Stable evaluators on identical tasks | Expected; use `--verbose` only when you need all rows |
| `run_cost_usd: delta=-0.0` with old baseline | Both sides had zero cost | Re-baseline after cost fix |

---

## Files touched (high level)

```
harnesslab/middleware/          # cache, circuit_breaker, tools, wrap, runtime
harnesslab/eval/                # cost.py, cost_evaluators.py, token_usage.py
harnesslab/gate/                  # baseline, check, significance
harnesslab/experiments/         # local_runner.py, target.py (usage callback)
harnesslab/cli/                   # gate_cli.py, compare_runner.py
harnesslab/report/pareto.py
examples/*/harnesses/           # cache.yaml, circuit_breaker.yaml
docs/GATE.md, docs/EVALUATORS.md, README.md
tests/                          # gate, cost, token_usage, local_runner, target_usage
```

---

## Follow-ups (not in this PR)

- Warn when benchmark and gate `--tasks` / `--task` flags do not match
- Gate blocking on `run_cost_usd` regression (optional flag)
- Commit a golden `benchmarks/incident-manager.json` for CI
