# Harnesses

A **harness** is a YAML configuration that wraps the same LangGraph agent with different execution policies — retries, context trimming, turn limits. HarnessLab A/B tests harness variants on identical tasks to answer: *did harness X beat harness Y, and why?*

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
  langsmith_project: triage
```

| Section | Controls |
|---|---|
| `execution` | `max_turns`, `stop_on_tool_error` |
| `tooling` | `retry_count`, `tool_timeout_s`, `error_format` |
| `context` | `history_limit` — trim messages before each LLM call |
| `observability` | `langsmith_project`, optional `trace_metadata` |

Harness files live in `examples/<agent>/harnesses/`.

---

## Shipped variants (ticket triage)

| Harness | Middleware | Best for |
|---|---|---|
| `minimal` | none | Baseline — no retries, no trimming |
| `retry` | tool retries (×2) | Flaky tool recovery (`T-011`, `T-015`) |
| `trim` | `history_limit: 8` | Long-context tasks (`T-012`) |

```bash
python -m harnesslab compare examples/ticket_triage --local -o report.html
python -m harnesslab compare examples/ticket_triage --harness minimal,retry,trim --dataset task_ablation
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
| **timeout** | Per-tool deadline enforcement | Slow external APIs (`fetch_metrics`) |
| **cache** | Memoize idempotent tool calls | Repeated runbook lookups |
| **fallback_model** | Downgrade model after N failures | Cost vs reliability on flaky arms |
| **checkpoint** | Persist/resume mid-task | Long incident investigations |
| **parallel_tools** | Fan-out independent tool calls | Multi-source correlation (`fetch_metrics` + `correlate_timeline`) |
| **circuit_breaker** | Stop calling a tool after N consecutive failures | Cascading outage scenarios |
| **rate_limit** | Cap tool calls per turn | Agents that over-search runbooks |

---

## Examples

| Agent | Path | Tasks | What makes it hard |
|---|---|---|---|
| Ticket triage | `examples/ticket_triage/` | `T-011`–`T-019` (9 stress tasks) | Flaky tools, SLA escalation, adversarial prompts |
| Incident analyst | `examples/incident_analyst/` | `I-101`–`I-106` (6 stress tasks) | Contradictory metrics, deploy correlation, security misdirection, long context |

```bash
# Ticket triage (support workflow)
python -m harnesslab compare examples/ticket_triage --local -o report.html

# Incident analyst (on-call workflow — more tools, trickier reasoning)
python -m harnesslab compare examples/incident_analyst --harness minimal,retry --local -o incident-report.html
python -m harnesslab compare examples/incident_analyst --task I-103 --local
```

The CLI loads `build_graph` from `examples/<agent>/graph.py` automatically — no code changes needed to add a third example.

See [EVALUATORS.md](EVALUATORS.md) for how harness differences show up in scores.
