# How HarnessLab maps to the stack

| Layer | In HarnessLab today |
|---|---|
| Prompt / context | Example `rules.py` system prompts; message history; optional `history_limit` trim |
| Harness | YAML under `examples/*/harnesses/` → `HarnessConfig` + middleware (retry, cache, circuit breaker, trim) |
| Loop | Default **react** topology: `agent` ↔ `tools` (+ optional `nudge`, `trim_context`) |
| Graph | Topology presets under `examples/*/graphs/` → `GraphConfig` + builders in `harnesslab/graph/topologies/` |

## Experiment dimensions

| CLI | Question |
|---|---|
| `--by harness` | Did harness X beat harness Y on the same graph? |
| `--by models` | Did model A beat model B on the same harness + graph? |
| `--by graphs` | Did topology X beat topology Y on the same harness + model? |

## Composition rule

- **Graph owns edges** (who runs next).
- **Harness wraps nodes / tools** (retries, cache, breaker, trim).
- Evaluators (`task_pass`, `graph_trajectory`, `coordination_pass`, …) score outcomes and paths so you can A/B any dimension.

Before this extension, topology was fixed and only harness/model were arms. Graph engineering makes topology a first-class arm without replacing harness engineering.
