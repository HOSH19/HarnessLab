# Topology patterns in HarnessLab

| Preset | Shape | When it helps |
|---|---|---|
| `react` | Single agent ↔ tools loop | Baseline; open-ended tool use |
| `pipeline` | Fixed stages (gather → analyze → finalize → optional verify) | Known order; verifier retry edge |
| `supervisor` | Supervisor routes to specialist workers, then synthesizes | Parallel evidence / role isolation |
| `plan_execute` | Planner → execute loop → critic / replan | Long-horizon work with explicit plan state |

## Handoff vs subgraph (conceptual)

- **Handoff:** agent A gives the conversation thread to B; B decides what happens next.
- **Subgraph / parent call:** parent invokes a specialist node and **keeps** control after it returns.

HarnessLab v1 supervisors use **declared parent routing** (topology you can export and score), not free-form agent-to-agent handoffs.

## Scoring paths

Tasks may set `expected_nodes` and `required_stages` so `graph_trajectory` and `coordination_pass` can compare topologies fairly. Specialist node names (`gather`, `supervisor`, `metrics_worker`, `planner`, …) appear in trajectories for multi-node graphs.
