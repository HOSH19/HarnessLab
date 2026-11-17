# Glossary

| Term | Meaning |
|---|---|
| **Node** | Unit of work: LLM agent, tools executor, router, verifier, or plain function |
| **Edge** | Allowed transition between nodes (fixed or conditional) |
| **State** | Shared typed snapshot that travels through the graph |
| **Harness** | Policy around a run: tools, retries, cache, circuit breaker, trim, observability |
| **Loop** | Observe–reason–act–verify cycle until a stop rule |
| **Topology** | The chosen graph shape (`react`, `pipeline`, `supervisor`, `plan_execute`) |
| **Trajectory** | Ordered list of node names visited during a run |
| **Send** | LangGraph API for dynamic fan-out to N downstream nodes |
| **Interrupt** | Pause for human-in-the-loop (documented; not a CLI UX in v1) |
| **Subgraph** | Nested graph invoked as a node; parent resumes after return |
| **Coordination** | Completing required stages in order (gather before draft, etc.) |
