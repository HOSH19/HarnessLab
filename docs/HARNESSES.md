# Harnesses

A **harness** is a YAML configuration that wraps the same LangGraph agent with different execution policies — retries, context trimming, turn limits. HarnessLab A/B tests harness variants on identical tasks to answer: *did harness X beat harness Y, and why?*

**You do not need new harness types per agent.** The same three presets (`minimal`, `retry`, `trim`) apply to every example. Each agent only needs its own `harnesses/` folder — mainly to set a distinct `langsmith_project` and optionally tune `max_turns` for simpler workflows.

---

## YAML schema

```yaml
name: minimal
execution:
  max_turns: 10
  stop_on_tool_error: false
tooling:
  retry_count: 0
  tool_timeout_s: 30
  error_format: minimal
context:
  history_limit: null
observability:
  langsmith_project: research-agent
```

| Section | Controls |
|---|---|
| `execution` | `max_turns`, `stop_on_tool_error` |
| `tooling` | `retry_count`, `tool_timeout_s`, `error_format` |
| `context` | `history_limit` — trim messages before each LLM call |
| `observability` | `langsmith_project`, optional `trace_metadata` |

Harness files live in `examples/<agent>/harnesses/`.

---

## Shipped variants (all examples)

| Harness | Middleware | Best for |
|---|---|---|
| `minimal` | none | Baseline — no retries, no trimming |
| `retry` | tool retries (×2) | Flaky tool recovery (`R-001`, `I-101`) |
| `trim` | `history_limit` | Long-context / multi-turn tasks (`I-104`) |

Research agent uses `max_turns: 8`; incident manager uses `max_turns: 12` — tuned per workflow complexity, not a new harness type.

```bash
python -m harnesslab compare examples/research_agent --local -o report.html
python -m harnesslab compare examples/incident_manager --harness minimal,retry,trim --local
```

---

## Logged fields (per run)

Five fields attached to each trace/output — kept minimal for LangSmith readability:

| Field | Layer | Purpose |
|---|---|---|
| `harness_name` | Trace tag | Groups runs by A/B arm |
| `classification` | Output | Primary correctness signal |
| `final_reply` | Output | Required reply terms |
| `graph_trajectory` | Output | Node path — explains behavioral differences |
| `error_count` | Output | Tool errors — stress-task retry differentiator |

`thread_id` is set internally for trajectory extraction. `error` is included only on invoke failure.

Task inputs and reference outputs (`expected_category`, `expected_nodes`, etc.) stay on LangSmith dataset examples — not duplicated into trace tags.

---

## Compare modes

| `--by` | Varies | Fixed |
|---|---|---|
| `harness` (default) | Harness YAML | Model from `HARNESSLAB_MODEL` |
| `models` | `nano`, `mini`, `turbo` | Single `--harness` |

---

## Future harness types

### Ready to add as YAML presets (no new code)

These only need a new file under `examples/<agent>/harnesses/`:

| Harness idea | Config lever | What it tests |
|---|---|---|
| **strict** | `max_turns: 5` | Early termination vs completeness |
| **patient** | `max_turns: 20`, `retry_count: 3` | Deep recovery on hard stress tasks (`I-103`, `I-106`) |
| **aggressive_trim** | `history_limit: 4` | Extreme context pressure (`I-104` conversation history) |
| **fail_fast** | `stop_on_tool_error: true` | Bail on first tool failure |
| **verbose_errors** | `error_format: verbose` | Whether richer tool errors help recovery |
| **no_retry_trim** | `retry_count: 0`, `history_limit: 6` | Isolate trim impact without retry masking |

### Needs new middleware (would require code)

| Harness idea | Mechanism | Use case |
|---|---|---|
| **timeout** | Per-tool deadline enforcement | Slow external APIs |
| **cache** | Memoize idempotent tool calls | Repeated literature/runbook lookups |
| **fallback_model** | Downgrade model after N failures | Cost vs reliability on flaky arms |
| **checkpoint** | Persist/resume mid-task | Long incident investigations |
| **parallel_tools** | Fan-out independent tool calls | Multi-source correlation |
| **circuit_breaker** | Stop calling a tool after N consecutive failures | Cascading outage scenarios |
| **rate_limit** | Cap tool calls per turn | Agents that over-search |

---

## Examples

| Agent | Path | Tasks | What makes it hard |
|---|---|---|---|
| Research agent | `examples/research_agent/` | `R-001`–`R-004` (4 tasks) | Straightforward workflow; one flaky search task |
| Incident manager | `examples/incident_manager/` | `I-101`–`I-106` (6 tasks) | Contradictory metrics, deploy correlation, security misdirection, long context |

```bash
# Easier — research workflow
python -m harnesslab compare examples/research_agent --local -o report.html

# Harder — on-call incident workflow
python -m harnesslab compare examples/incident_manager --harness minimal,retry --local -o incident-report.html
python -m harnesslab compare examples/incident_manager --task I-103 --local
```

The CLI loads `build_graph` from `examples/<agent>/graph.py` automatically — no code changes needed to add a third example.

See [EVALUATORS.md](EVALUATORS.md) for how harness differences show up in scores.
