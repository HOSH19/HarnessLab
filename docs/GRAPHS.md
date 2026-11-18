# Graphs

A **graph** is a topology preset: which nodes exist, how edges route work, and what shared state travels between them. HarnessLab A/B tests graph variants on identical tasks to answer: *did topology X beat topology Y, and why?*

**Harnesses wrap nodes/tools. Graphs own edges.** Use `--by harness` to compare retries/cache/trim; use `--by graphs` to compare react vs pipeline vs supervisor vs plan-execute on a fixed harness + model.

Learning notes: [notes/](../notes/).

---

## YAML schema

```yaml
name: supervisor
topology: supervisor   # react | pipeline | supervisor | plan_execute
roles: {}              # optional role -> system prompt overrides
max_workers: 3
require_verifier: false
expected_nodes:
  - intake
  - metrics_worker
  - finalize
```

Graph files live in `examples/<agent>/graphs/`.

---

## Shipped presets

| Preset | Topology | Intent |
|---|---|---|
| `react` | Single agent ↔ tools | Baseline loop |
| `pipeline` | gather → analyze → finalize | Fixed stages |
| `pipeline_verify` | pipeline + verify→retry | Incomplete drafts get another finalize pass |
| `supervisor` | intake → specialists → synthesize → finalize | Role isolation / coordination |
| `plan_execute` | planner → executor → critic / replan | Explicit plan state |

---

## CLI

```bash
# Topology A/B (fixed harness + model)
python -m harnesslab compare examples/incident_manager \
  --by graphs --graph react,pipeline,supervisor --harness minimal --local

# One graph on one harness
python -m harnesslab run examples/incident_manager \
  --harness minimal --graph supervisor --local --task I-107

# Gate / benchmark on graph arms
python -m harnesslab benchmark examples/incident_manager \
  --by graphs --graph react,pipeline --harness minimal --local -o baselines/graphs.json
python -m harnesslab gate examples/incident_manager \
  --by graphs --graph react,pipeline --harness minimal \
  --baseline baselines/graphs.json --local
```

---

## Composition with harnesses

| Concern | Owner |
|---|---|
| Retries, cache, circuit breaker, trim | Harness middleware |
| Stage order, specialist nodes, verify/replan edges | Graph topology |
| Trajectory / coordination scoring | Evaluators (`graph_trajectory`, `coordination_pass`) |

See also: [HARNESSES.md](HARNESSES.md) · [EVALUATORS.md](EVALUATORS.md) · [GATE.md](GATE.md).

---

## LangSmith notes

- Experiments use dataset **`graph engineering`**. Open the **newest** experiment after a compare.
- **TTFT**: LangSmith’s built-in **Time to First Token** column often stays blank for agent `evaluate` rows. HarnessLab still streams + marks root `new_token`, and publishes feedback **`ttft_seconds`** so the table shows a numeric TTFT cell. Look for that feedback column on the newest experiment.
- **Deprecated API warning** (removal Jan 31, 2027): upstream `langsmith.evaluate` still prefers legacy `list_runs` on dual ClickHouse+SmithDB Cloud backends ([langsmith-python#108](https://github.com/langchain-ai/langsmith-python/issues/108)). HarnessLab applies `prefer_smithdb_experiment_traces()` before evaluate so experiment trace loads use SmithDB v2 instead. Historical key usage from older runs/scripts can linger on the dashboard until it ages out; keep `langsmith>=0.14.17`.
