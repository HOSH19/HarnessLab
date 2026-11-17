# Loop vs graph

## Loop engineering

Design the repeated cycle a **single** agent runs: gather context, act with tools, verify, repeat until a stop condition.

Hard parts: independent verification, budgets, and stop rules that do not trust the model's claim that it is “done.”

Use a loop when:

- One bounded task with local tool feedback
- Few specialties; order can be left to the model
- You want maximum flexibility with minimal topology design

## Graph engineering

Make control flow **explicit**: named nodes, allowed edges, shared typed state. Nodes can be agentic, deterministic, routers, or human checkpoints. Edges can be fixed, conditional, cyclic (retry), or dynamic (`Send` fan-out).

Use a graph when:

- Work splits into specialties that should not share full context
- You need parallel-then-join, independent verification, or auditable paths
- Routing itself is a product decision (not only an LLM judgment)

## Important correction

**Graph engineering is not synonymous with multi-agent.** Multi-agent systems are usually graphs whose nodes are agents. A single-agent pipeline with deterministic validators is also graph engineering.

Graphs **wrap** loops; they do not obsolete them. Each agentic node still needs a local loop and a harness.

See also: [LangChain — 3 years of graph engineering](https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph), [DataCamp guide](https://www.datacamp.com/tutorial/graph-engineering-guide).
