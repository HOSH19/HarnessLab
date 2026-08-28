# HarnessLab Run Analysis

**Generated:** 2026-08-28  
**Runs analyzed:** 2 (all remaining under `.harnesslab/runs/`)  
**Old runs deleted:** 10

| Run directory | Dataset | Compare by | Config |
|---|---|---|---|
| `2026-08-28T22-20-47_harness` | `different_harness` | harness | `gpt-4.1-nano`, minimal vs retry, 2 tasks |
| `2026-08-28T22-20-01_models` | `different_models` | models | minimal harness, nano / mini / turbo, 2 tasks |

Both runs use the `ticket_triage` example, LangSmith mode, and the same two task fixtures: **T-012** (long multi-turn conversation, refund triage) and **T-011** (flaky `read_ticket` with 2 failures before success).

---

## 1. Harness Compare (`different_harness`)

**Run:** `2026-08-28T22-20-47_harness`  
**Model:** `gpt-4.1-nano` fixed across arms  
**Arms:** `minimal` vs `retry`

### Per-metric averages (from `summary.json`)

| Metric | minimal | retry | Winner |
|---|---:|---:|---|
| **task_pass** | **0.875** | 0.750 | **minimal** (+0.125) |
| **tool_sequence** | 0.500 | 0.500 | tie |
| **graph_trajectory** | **0.896** | 0.771 | **minimal** (+0.125) |
| **failure_fingerprint** | **1.000** | 0.500 | **minimal** (+0.500) |
| efficiency | 1.000 | 1.000 | tie (saturated) |
| error_recovery | 1.000 | 1.000 | tie (saturated) |
| step_count | 1.000 | 1.000 | tie (saturated) |

**Headline:** `minimal` wins on all four requested discriminative metrics. `retry` adds no measurable benefit on this 2-task slice and actively hurts T-012.

### Per-task breakdown

#### T-012 — context-heavy refund ticket

Long `conversation_history` (14 turns) ending with "Triage ticket T-012 using everything we discussed above."

| Metric | minimal | retry |
|---|---|---|
| task_pass | 0.75 — `category_ok=True, terms_ok=False, terms_score=0.50` | 0.50 — `category_ok=True, terms_ok=False, terms_score=0.00` |
| tool_sequence | 0.0 — actual: `[read_ticket, check_sla, classify, draft_reply]`; expected `search_kb` missing | 0.0 — actual: `[read_ticket, check_sla, classify]`; stopped before `draft_reply` |
| graph_trajectory | 0.875 — progress 0.88, 8 nodes | 0.625 — progress 0.62, 6 nodes (shorter, incomplete) |
| failure_fingerprint | SUCCESS | **WRONG_ANSWER** |

**Evaluator comments (key):**
- Both arms get category right but miss required reply terms on T-012; `retry` misses all terms (`terms_score=0.00`).
- Both substitute `check_sla` for `search_kb` in the tool chain, failing strict tool-sequence scoring.
- `retry` terminates earlier (no `draft_reply`), producing `WRONG_ANSWER` fingerprint and lower trajectory progress.

#### T-011 — flaky tool recovery

`flaky_tools: { read_ticket: 2 }` — `read_ticket` fails twice before succeeding.

| Metric | minimal | retry |
|---|---|---|
| task_pass | 1.00 — `category_ok=True, terms_ok=True` | 1.00 — same |
| tool_sequence | 1.00 — `[read_ticket, check_sla, search_kb, classify, draft_reply]` (extra `check_sla` OK as subsequence) | 1.00 — same sequence |
| graph_trajectory | 0.917 — progress 0.92 | 0.917 — same |
| failure_fingerprint | SUCCESS | SUCCESS |

**Evaluator comments (key):**
- Identical outcomes on T-011; both harnesses recover from flaky `read_ticket` and complete the full pipeline.
- Extra `check_sla` call is tolerated because `tool_sequence` scores subsequence match, not exact equality.

### Metrics always at 1.0 (evaluator design)

| Metric | Why always 1.0 in these runs |
|---|---|
| **efficiency** | Starts at 1.0; only penalizes latency > 20 s, tokens > 3000, or child runs > `expected_max_steps`. All runs: 2.7–6.2 s latency, `tokens=0` (not captured in LangSmith metadata), `steps=1` child run. |
| **error_recovery** | Binary pass when `error_count ≤ max_acceptable_errors` (default 0). All runs report `error_count=0`. |
| **step_count** | Binary pass when `child_count ≤ expected_max_steps` (default 12). All runs report `steps=1`. |

These three metrics are **not discriminative** at current thresholds and dataset scale. They will only diverge under high latency, token blow-up, or step-count violations.

### Actionable findings for portfolio

1. **Ship `minimal` over `retry` for ticket triage** — higher task_pass, trajectory, and failure_fingerprint on the harder T-012 task with no regression on T-011.
2. **T-012 is the stress test** — long-context recall drives term-matching failures and tool-choice errors (`check_sla` vs `search_kb`). Prioritize this scenario in harness iteration.
3. **`retry` harness regresses on hard tasks** — shorter trajectories and `WRONG_ANSWER` on T-012 suggest retry logic may truncate or derail multi-step flows; investigate before promoting.
4. **Tool-sequence scoring is brittle on T-012** — both harnesses fail (0.0) because `search_kb` is skipped; consider whether `check_sla` is an acceptable substitute or tighten agent prompts.
5. **Operational metrics are saturated** — do not use efficiency / error_recovery / step_count to compare arms until thresholds tighten or tasks induce errors and long runs.

---

## 2. Model Compare (`different_models`)

**Run:** `2026-08-28T22-20-01_models`  
**Harness:** `minimal` fixed across arms  
**Arms:** `gpt-4.1-nano`, `gpt-4.1-mini`, `gpt-3.5-turbo`

### Per-metric averages (from `summary.json`)

| Metric | nano | mini | turbo | Best | Worst |
|---|---:|---:|---:|---|---|
| **task_pass** | **0.875** | **0.875** | 0.810 | nano & mini (tie) | turbo |
| **tool_sequence** | 0.500 | **1.000** | **1.000** | mini & turbo | nano |
| **graph_trajectory** | **0.896** | 0.771 | 0.875 | nano | mini |
| **failure_fingerprint** | 1.000 | 1.000 | 1.000 | all tie | — |
| efficiency | 1.000 | 1.000 | 1.000 | saturated | — |
| error_recovery | 1.000 | 1.000 | 1.000 | saturated | — |
| step_count | 1.000 | 1.000 | 1.000 | saturated | — |

### Per-task breakdown

#### T-012 — context-heavy refund ticket

| Metric | nano | mini | turbo |
|---|---:|---:|---:|
| task_pass | 0.75 (`terms_score=0.50`) | 0.75 (`terms_score=0.50`) | **0.62** (`terms_score=0.25`) |
| tool_sequence | **0.0** — skipped `search_kb`, used `check_sla` | 1.0 — duplicate `search_kb` call tolerated | 1.0 — exact expected sequence |
| graph_trajectory | 0.875 | 0.625 | **1.0** (`matched=True`) |
| failure_fingerprint | SUCCESS | SUCCESS | SUCCESS |

**Key comments:**
- **turbo** has worst correctness (lowest term coverage) but best operational path on T-012 (perfect tool sequence and graph match).
- **nano** has worst tool discipline (0.0 tool_sequence) on T-012.
- **mini** gets tool_sequence credit via subsequence (duplicate `search_kb`) but lower graph progress (0.625).

#### T-011 — flaky tool recovery

| Metric | nano | mini | turbo |
|---|---:|---:|---:|
| task_pass | 1.00 | 1.00 | 1.00 |
| tool_sequence | 1.00 | 1.00 | 1.00 |
| graph_trajectory | 0.917 | 0.917 | 0.750 |
| failure_fingerprint | SUCCESS | SUCCESS | SUCCESS |

**Key comments:**
- All models pass T-011 on correctness.
- **turbo** has lowest graph_trajectory (0.75) despite correct tools — more agent↔tools oscillation (10 nodes vs 12 for nano/mini).
- **nano** and **mini** tie on T-011 across correctness and trajectory.

### Correctness vs operational split

| Dimension | Best | Worst | Notes |
|---|---|---|---|
| **Correctness** (task_pass) | nano & mini (0.875) | turbo (0.810) | turbo loses on T-012 term recall (`terms_score=0.25`) |
| **Tool discipline** (tool_sequence) | mini & turbo (1.0) | nano (0.5) | nano skips `search_kb` on T-012 |
| **Graph efficiency** (graph_trajectory) | nano (0.896) | mini (0.771) | nano leads overall despite T-012 tool miss |
| **Failure rate** (failure_fingerprint) | all (1.0) | — | No model produced `WRONG_ANSWER` under minimal harness |

**Trade-off summary:** No single model dominates. **nano** leads on correctness and graph progress but fails tool-sequence on hard context. **turbo** is most operationally clean on T-012 tools/trajectory but weakest on reply term recall. **mini** is the balanced middle — perfect tool_sequence average, tied-best task_pass, weakest graph_trajectory.

---

## 3. Cross-cutting analysis

### Are evaluators trustworthy?

**Partially.** Scores in `summary.json` and per-row `evaluation_results` are internally consistent and evaluator comments are informative. However:

| Issue | Severity | Detail |
|---|---|---|
| **Empty `outputs` in stored rows** | High | Every row in all arm JSON files has `"outputs": {}`. Evaluators ran against live LangSmith `Run` objects at experiment time (comments reference real tool lists and scores), but persisted artifacts drop agent outputs. Cannot audit correctness from stored files alone. |
| **`tokens=0` everywhere** | Medium | `efficiency` never penalizes token usage because LangSmith runs lack token metadata in this setup. Metric is latency-only in practice. |
| **`steps=1` everywhere** | Medium | `run_child_count` returns 1 (top-level run only); inner agent/tool loop steps are in `graph_trajectory`, not child runs. `step_count` and efficiency step penalty are non-discriminative. |
| **Saturated pass metrics** | Medium | efficiency, error_recovery, step_count are 1.0 across all 10 arm×task combinations. Portfolio comparisons must rely on task_pass, tool_sequence, graph_trajectory, failure_fingerprint. |
| **failure_fingerprint binary** | Low | Coarse SUCCESS/WRONG_ANSWER; only `retry` on T-012 triggered failure. Useful as a gate, not for fine ranking. |
| **tool_sequence subsequence semantics** | Low (by design) | Extra tools (e.g. `check_sla`) pass if expected tools appear in order. Explains mini passing with duplicate `search_kb` but nano failing when `search_kb` is absent entirely. |

### Bugs observed

1. **Storage bug: missing outputs** — all 12 stored task rows (6 per run × 2 tasks, across all arms) have empty `outputs`. Fix the runner/store layer to persist `classification`, `final_reply`, `graph_trajectory`, and tool messages for post-hoc review.
2. **Token reporting gap** — efficiency comments show `tokens=0` for every run; either wire token metadata from the LLM provider or remove token thresholds from the scorer until available.
3. **Child-run counting** — `steps=1` does not reflect agent↔tools loop depth; graph_trajectory captures this better. Consider aligning step_count with graph node count or LangGraph step metadata.

### Recommendations for next scrutiny steps

1. **Fix output persistence** — re-run after patching store so `docs/RUN_ANALYSIS.md`-style reviews can inspect actual `final_reply` text and tool traces without LangSmith UI.
2. **Expand T-012 coverage** — run full dataset (not `tasks_limit=2`) to confirm minimal > retry and nano tool-sequence failure rate on context-heavy tickets.
3. **Tighten saturated evaluators** — lower efficiency latency threshold, require token metadata, or score step_count from graph_trajectory length so operational metrics differentiate arms.
4. **Add term-recall ablation on T-012** — turbo's `terms_score=0.25` vs nano/mini `0.50` warrants inspecting which required terms each model omits in the draft reply.
5. **Investigate `retry` harness on T-012** — determine why trajectory stops at `classify` (no `draft_reply`) and whether retry policy causes early termination on long-context inputs.
6. **Re-evaluate `check_sla` substitution** — decide if skipping `search_kb` should be a partial tool_sequence score rather than binary 0.0, since both harnesses prefer SLA check on refund tickets.

---

## Appendix: run manifests

### `2026-08-28T22-20-47_harness`

```json
{
  "dataset": "different_harness",
  "compare_by": "harness",
  "model": "gpt-4.1-nano",
  "harnesses": ["minimal", "retry"],
  "task_count": 2,
  "timestamp": "2026-08-28T22:20:47.712955+00:00"
}
```

### `2026-08-28T22-20-01_models`

```json
{
  "dataset": "different_models",
  "compare_by": "models",
  "harness": "minimal",
  "models": ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-3.5-turbo"],
  "task_count": 2,
  "timestamp": "2026-08-28T22:20:01.195330+00:00"
}
```
