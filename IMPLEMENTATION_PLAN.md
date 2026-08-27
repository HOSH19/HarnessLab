# HarnessLab Implementation Plan

Project phases, scope boundaries, and delivery checklist.

## Phase overview

```mermaid
gantt
    title HarnessLab delivery phases
    dateFormat YYYY-MM-DD
    section Phase1
    Core harness + CLI draft           :done, p1, 2026-08-27, 7d
    section Phase2
    Evals + 10 tasks + dataset upload  :active, p2, 2026-08-27, 7d
    section Phase3
    CI + polish + optional PyPI        :p3, after p2, 7d
```

## Phase 1 — Core harness (complete)

```mermaid
flowchart LR
    YAML[harness YAML] --> Config[Pydantic config]
    Config --> Builder[graph builder]
    Builder --> Graph[LangGraph agent]
    Graph --> CLI[run / compare]
```

| Deliverable | Status |
|---|---|
| Package layout (`config`, `graph`, `middleware`, `eval`, `cli`) | done |
| Harness YAML schema + loader | done |
| Middleware: limits, retry, context trim | done |
| Ticket triage example agent | done |
| `harnesslab run` + `harnesslab compare` | done |
| HTML comparison report | done |
| README with architecture diagrams | done |

## Phase 2 — Evals and dataset (current)

```mermaid
flowchart TB
    Graph[LangGraph invoke] --> Trajectory[extract_langgraph_trajectory_from_thread]
    Graph --> Parse[extract_fields_from_messages]
    Trajectory --> Eval[graph_trajectory scorer]
    Parse --> Eval2[task_pass scorer]
    Eval --> LS[LangSmith evaluate]
    Eval2 --> LS
    Tasks[10 task fixtures] --> LS
    LS --> Report[HTML report]
```

| Deliverable | Status |
|---|---|
| Graph trajectory extraction via agentevals | done |
| `graph_trajectory` evaluator (node subsequence match) | done |
| Tool output parsing for `task_pass` | done |
| 10 ticket fixtures + 10 task JSON files | done |
| `harnesslab dataset upload` command | done |
| `--tasks` limit flag for smoke runs | done |
| Unit tests for trajectory + extraction | done |

## Phase 3 — Portfolio polish (next)

```mermaid
flowchart LR
    PR[Pull request] --> CI[GitHub Actions]
    CI --> Smoke[harnesslab compare --local --tasks 2]
    Smoke --> Report[artifact report.html]
    Report --> README[README demo update]
```

| Deliverable | Status |
|---|---|
| GitHub Actions smoke workflow | pending |
| README demo GIF or recorded output | pending |
| Optional PyPI publish | pending |
| Verification middleware (`verify.py`) | deferred |
| Human-in-the-loop interrupts | deferred |
| Persistent checkpointer sessions | deferred |

## Scope matrix

### In scope

```mermaid
mindmap
  root((In scope))
    Harness
      YAML configs
      retry middleware
      context trim
      recursion limits
    Runtime
      LangGraph StateGraph
      MemorySaver
    Observability
      LangSmith tracing
      LangSmith evaluate
    Evaluators
      task_pass
      graph_trajectory
      efficiency
      failure_fingerprint
    Demo
      ticket triage agent
      10 tasks
      3 harness variants
    Tooling
      run
      compare
      dataset upload
```

### Out of scope

```mermaid
mindmap
  root((Out of scope))
    v0.1 excluded
      Langfuse
      multi agent orchestration
      LLM summarization middleware
      charting libraries
      production sandboxing
    deferred v2
      verification node
      human approval interrupts
      harnesslab init scaffolder
      graph trajectory LLM judge
      Harness Card manifest export
```

## Architecture boundaries

```mermaid
flowchart TB
    subgraph cli_layer [cli]
        CLI[Typer commands]
    end

    subgraph orchestration [experiments]
        Runner[runner.py]
        Dataset[dataset.py]
    end

    subgraph scoring [eval]
        Outcome[outcome.py]
        Trajectory[trajectory.py]
        Efficiency[efficiency.py]
        Fingerprint[fingerprint.py]
    end

    subgraph runtime [graph + middleware]
        Builder[builder.py]
        Extract[extract.py]
        MW[middleware/*]
    end

    CLI --> Runner
    CLI --> Dataset
    Runner --> Builder
    Runner --> Extract
    Runner --> Outcome
    Runner --> Trajectory
    Runner --> Efficiency
    Runner --> Fingerprint
```

| Module | Owns | Does not own |
|---|---|---|
| `config/` | YAML schema + validation | graph compile |
| `graph/` | state, edges, builder, extract | tools, prompts |
| `middleware/` | harness node behavior | eval logic |
| `eval/` | scorer functions | experiment orchestration |
| `experiments/` | LangSmith run/upload | scorer implementation |
| `report/` | HTML formatting | experiment execution |
| `cli/` | argument parsing | business logic |
| `examples/` | demo agent + fixtures | library internals |

## Code hygiene rules

| Rule | Target |
|---|---|
| Module size | max ~150 lines |
| Function size | max ~25 lines |
| File docs | module docstring required |
| Function docs | public functions documented |
| Comments | no single-line `#` comments |
| Separation | CLI stays thin, logic in packages |

## Research motivation

```mermaid
flowchart LR
    Model[Same model] --> H1[Harness A]
    Model --> H2[Harness B]
    H1 --> Score1[pass rate + cost + failures]
    H2 --> Score2[pass rate + cost + failures]
    Score1 --> Compare[A/B report]
    Score2 --> Compare
```

HarnessLab makes harness configuration explicit so benchmark gains are not misattributed to model improvements alone.

References:
- [Stop Comparing LLM Agents Without Disclosing the Harness](https://arxiv.org/html/2605.23950)
- [Harness-Bench](https://doi.org/10.48550/arxiv.2605.27922)
- [Scaffold Effect in Coding Agents](https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/assets/papers/74_The_Scaffold_Effect_in_Codi.pdf)

## Commands by phase

| Phase | Command |
|---|---|
| 1 | `harnesslab run examples/ticket_triage --harness minimal` |
| 1 | `harnesslab compare examples/ticket_triage --local` |
| 2 | `harnesslab dataset upload examples/ticket_triage` |
| 2 | `harnesslab compare examples/ticket_triage --tasks 2 --local` |
| 3 | CI smoke via GitHub Actions |

## Success criteria

- [x] Phase 1 core harness + CLI
- [x] Phase 2 graph trajectory evals + 10 tasks
- [ ] Phase 3 CI workflow
- [ ] Phase 3 optional PyPI publish
