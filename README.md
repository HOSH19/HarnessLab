# HarnessLab

[![CI](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml/badge.svg)](https://github.com/HOSH19/HarnessLab/actions/workflows/ci.yml)

> Declare harness variants as YAML. Run LangGraph A/B experiments. Score with LangSmith.

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for phased delivery, scope, and architecture boundaries.
See [docs/DEMO.md](docs/DEMO.md) for example terminal output and report preview.

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
conda create -n harnesslab python=3.11 -y && conda activate harnesslab
pip install -e ".[dev]"

cp .env.example .env
# edit .env with your keys (this file is gitignored)

harnesslab compare examples/ticket_triage --local --tasks 2 -o report.html
```

Or with `venv`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
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

## CI

```mermaid
flowchart LR
    Push[push to main] --> Unit[pytest]
    Unit --> Smoke[compare --local --tasks 2]
    Smoke --> Artifact[report.html artifact]
```

| Job | Runs on | Needs |
|---|---|---|
| `unit-tests` | every push + PR | nothing |
| `smoke-compare` | push to `main` + manual dispatch | `OPENAI_API_KEY` secret |

Add `OPENAI_API_KEY` under **Settings → Secrets and variables → Actions** to enable the smoke job.

## Demo output

```text
Evaluating harness: minimal
Evaluating harness: with_retry
Report written to report.html
```

| Harness | task_pass | graph_trajectory | efficiency | failure_fingerprint |
|---|---|---|---|---|
| minimal | varies | varies | varies | varies |
| with_retry | varies | varies | varies | varies |

Full example: [docs/DEMO.md](docs/DEMO.md)

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
mindmap
  root((Not in v0.1))
    Deferred middleware
      verification middleware
      LLM summarization
    Deferred runtime
      human in the loop
      persistent memory
    Deferred evals
      graph trajectory LLM judge
    Excluded integrations
      Langfuse
    Excluded orchestration
      multi agent orchestration
    Excluded tooling
      harnesslab init scaffolder
      charting libraries
      production sandboxing
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

Put these in a local `.env` file (gitignored) or export them in your shell.
GitHub Actions uses repository secrets instead of `.env`.

## Research context

Harness choice is a hidden variable in agent benchmarks. HarnessLab makes harness config explicit and measurable — same model, different harness, compare in LangSmith.

## License

MIT
