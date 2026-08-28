# Scrutiny follow-up (T-018 / T-019 suite)

## Why LangSmith showed `ai:` in Outputs

LangSmith was rendering raw LangChain `AIMessage` objects from the `messages` field in run outputs. Those objects stringify as `ai: ...`, which became the Outputs column header text.

**Fix:** runner now sets a clean `output` field (`classification: final_reply`) and serializes `messages` to JSON-safe dicts without role prefixes.

## Completed scrutiny items

| Item | Status |
|---|---|
| Fix output persistence (`run.outputs` fallback in store) | Done |
| Expand T-012 coverage | Skipped (suite is T-018/T-019 only) |
| Tighten saturated evaluators (efficiency, step_count from trajectory) | Done |
| Term-recall ablation (`missing_terms` in `task_pass` comment) | Done |
| Investigate retry early-stop | Documented below |
| Partial `tool_sequence` credit | Done (`subsequence_progress`) |

## Retry harness behavior

`retry` wraps the tool node and re-invokes on exceptions. It does **not** retry when the model simply stops early (no `draft_reply` tool call). On T-018/T-019, early termination is a model decision, not a retry-loop bug — but `retry` adds latency on flaky tools which can consume the turn budget on `minimal` (10 turns) vs tasks needing 7+ tool rounds.

**Portfolio note:** prefer `minimal` unless flaky-tool recovery is the explicit test (T-018 with `search_kb` / `escalate_ticket` flakes).

## Re-run after fixes

```bash
harnesslab compare examples/ticket_triage --dataset different_harness -o report.html
harnesslab compare examples/ticket_triage --by models --dataset different_models -o report.html
```

Local JSON under `.harnesslab/runs/` will now include `outputs.final_reply`, `outputs.output`, and serialized `messages`.
