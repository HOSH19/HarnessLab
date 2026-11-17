# The agent engineering stack

Each layer controls something the layer below it cannot. Layers **stack**; they do not replace each other.

| Layer | Controls | Design unit |
|---|---|---|
| Prompt engineering | One model response | Instructions |
| Context engineering | What the model can see | Retrieval, memory, window budget |
| **Harness engineering** | What one run may use | Tools, caps, retries, observability |
| **Loop engineering** | One agent's observe–reason–act–verify cycle | Trigger, success criterion, stop rule |
| **Graph engineering** | Explicit execution topology | Nodes, edges, shared state |

## How they compose

- A **graph** decides which nodes exist and how work moves (branch, join, retry, parallel fan-out).
- Each **agentic node** still runs a **loop** (plan → act → observe → stop).
- That loop runs inside a **harness** (tools, middleware, budgets, traces).
- Inside each model call: **context** and **prompt**.

A loop is the simplest cyclic graph (one node with an edge back to itself). Graph engineering starts when you deliberately add nodes and constrain transitions.

## Two meanings of “graph”

1. **Task / agent graph** (this project) — nodes are work units; edges are control flow.
2. **Knowledge graph** — nodes are entities/facts; edges are relations (memory / GraphRAG). Different discipline; out of scope for HarnessLab v1.

Sources: [Ryzo — Graph Engineering](https://www.ryzo.nl/resources/blog/graph-engineering), [arxiv survey](https://arxiv.org/html/2608.21156v2), [TrueFoundry / loops & graphs](https://www.truefoundry.com/blog/andrew-ng-loop-graph-engineering-production).
