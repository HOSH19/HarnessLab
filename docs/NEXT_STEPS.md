# Next steps

HarnessLab is a working harness A/B framework on a single demo agent. Suggested priorities:

## 1. Prove the harness delta on the full stress suite

Run all 9 tasks (`T-011`–`T-019`) with `minimal`, `retry`, and `trim` on a fixed model and publish results to LangSmith dataset `task_ablation`:

```bash
python -m harnesslab dataset upload examples/ticket_triage --name task_ablation
python -m harnesslab compare examples/ticket_triage --dataset task_ablation -o report.html
```

**Goal:** a clear answer on which harness wins per task category (flaky recovery, long context, SLA, adversarial).

## 2. Second example agent

The framework is agent-agnostic but only ships `ticket_triage`. Add a smaller second example (e.g. a 2-tool research or summarization agent) to validate that harness YAML + evaluators generalize beyond triage.

## 3. `harnesslab init` scaffolder

Generate `harnesses/`, `tasks/`, and a minimal `graph.py` for a new project. Lowers the cost of adopting HarnessLab on a real internal agent.

## 4. CI hardening

- Run compare on `main` with `--local --tasks 2` (already in CI)
- Optional: nightly full-suite upload to LangSmith with repo secrets

## 5. PyPI publish (optional)

Package is installable via `pip install -e .`; publishing to PyPI would make distribution easier for teams not cloning the repo.

## Out of scope (for now)

- Langfuse / alternate observability backends
- Multi-tenant or hosted UI beyond LangSmith + `report.html`
- LLM-as-judge evaluators (current scorers are deterministic)
