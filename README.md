# HarnessLab

> Declare harness variants as YAML. Run LangGraph A/B experiments. Score with LangSmith.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for phased delivery, scope, and architecture boundaries.

```mermaid
flowchart LR
    YAML[harnesses/*.yaml] --> Builder[graph_builder]
    Graph[LangGraph agent] --> Builder
    Builder --> Run[invoke per task]
    Run --> LS[LangSmith traces]
    LS --> Eval[evaluators]
    Eval --> Report[HTML report]
```

## Quick start

```bash
cd harnesslab
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export OPENAI_API_KEY=...
export LANGSMITH_API_KEY=...
export LANGSMITH_TRACING=true

harnesslab compare examples/ticket_triage --local -o report.html
```

## Architecture

```mermaid
flowchart TB
    subgraph harnesslab [HarnessLab]
        configPkg[config/]
        graphPkg[graph/]
        middlewarePkg[middleware/]
        evalPkg[eval/]
        experimentsPkg[experiments/]
        cliPkg[cli/]
    end

    subgraph external [External]
        LG[LangGraph]
        LS[LangSmith]
        OAI[OpenAI API]
    end

    cliPkg --> experimentsPkg
    experimentsPkg --> graphPkg
    graphPkg --> middlewarePkg
    graphPkg --> LG
    experimentsPkg --> evalPkg
    experimentsPkg --> LS
    graphPkg --> OAI
```

## Harness A/B flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Builder
    participant Graph
    participant LangSmith

    User->>CLI: compare --harness minimal,with_retry
    loop each harness variant
        CLI->>Builder: load YAML config
        Builder->>Graph: compile with middleware
        CLI->>LangSmith: evaluate(tasks)
        Graph->>LangSmith: trace per node
        LangSmith-->>CLI: experiment results
    end
    CLI->>User: report.html
```

## Example agent

```mermaid
flowchart LR
    Start([start]) --> Trim{history_limit?}
    Trim -->|yes| Agent
    Trim -->|no| Agent
    Agent -->|tool_calls| Tools
    Tools -->|retry middleware| Agent
    Agent -->|done| End([end])
```

| Tool | Purpose |
|---|---|
| `read_ticket` | Load ticket from fixtures |
| `search_kb` | Match KB articles |
| `classify` | Assign category |
| `draft_reply` | Write customer reply |

## Harness configs

| Variant | `max_turns` | `retry_count` | `history_limit` |
|---|---|---|---|
| `minimal` | 10 | 0 | none |
| `with_retry` | 15 | 2 | none |
| `with_context_trim` | 15 | 0 | 8 |

## Evaluators

```mermaid
flowchart LR
    Run[LangSmith Run] --> TP[task_pass]
    Run --> GT[graph_trajectory]
    Run --> EF[efficiency]
    Run --> FF[failure_fingerprint]
    TP --> Score[experiment score]
    GT --> Score
    EF --> Score
    FF --> Score
```

| Evaluator | Type | Measures |
|---|---|---|
| `task_pass` | deterministic | correct category + reply terms |
| `graph_trajectory` | deterministic | expected graph nodes in order |
| `efficiency` | deterministic | latency, tokens, steps |
| `failure_fingerprint` | deterministic | TIMEOUT / TOOL_ERROR / WRONG_ANSWER / SUCCESS |

## CLI

```bash
harnesslab run examples/ticket_triage --harness minimal
harnesslab compare examples/ticket_triage --harness minimal,with_retry --output report.html
harnesslab compare examples/ticket_triage --local --tasks 2
harnesslab dataset upload examples/ticket_triage --name harnesslab-ticket-triage
```

## In scope (v0.1)

```mermaid
mindmap
  root((HarnessLab v0.1))
    Harness layers
      max_turns
      tool retry
      context trim
    Runtime
      LangGraph StateGraph
      MemorySaver checkpointer
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
      3 harness YAML configs
      10 task fixtures
    Output
      HTML comparison table
      CLI run and compare
```

## Out of scope (v0.1)

```mermaid
flowchart TB
    Root((Not in v0.1))
    Root --> Deferred[Deferred]
    Root --> Excluded[Explicitly excluded]

    Deferred --> D1[verification middleware]
    Deferred --> D2[LLM summarization]
    Deferred --> D3[human in the loop]
    Deferred --> D4[persistent memory]
    Deferred --> D5[graph trajectory LLM judge]

    Excluded --> E1[Langfuse]
    Excluded --> E2[multi agent orchestration]
    Excluded --> E3[PyPI publish]
    Excluded --> E4[harnesslab init scaffolder]
    Excluded --> E5[charting libraries]
    Excluded --> E6[production sandboxing]
```

## Project layout

```
harnesslab/
├── harnesslab/
│   ├── config/         # YAML schema + loader
│   ├── graph/          # builder, state, edges
│   ├── middleware/     # retry, context, limits
│   ├── eval/           # LangSmith scorers
│   ├── experiments/    # runner + task loader
│   ├── report/         # HTML output
│   └── cli/            # typer commands
├── examples/ticket_triage/
│   ├── graph.py        # demo agent
│   ├── tools.py
│   ├── harnesses/      # YAML variants
│   ├── tasks/          # eval fixtures
│   └── fixtures/       # mock data
└── tests/
```

## Environment

| Variable | Required | Default |
|---|---|---|
| `OPENAI_API_KEY` | yes | — |
| `LANGSMITH_API_KEY` | yes (unless `--local`) | — |
| `LANGSMITH_TRACING` | recommended | `true` |
| `HARNESSLAB_MODEL` | no | `gpt-4o-mini` |

## Research context

Harness choice is a hidden variable in agent benchmarks. HarnessLab makes harness config explicit and measurable — same model, different harness, compare in LangSmith.

## License

MIT
