# HarnessLab Evaluators

HarnessLab scores every agent run on **five evaluators**. Together they answer: *did harness/model/graph X beat Y on task Z, and why?*

These are **feedback scores** uploaded to LangSmith (or stored in local JSON). They are separate from the [five logged output fields](HARNESSES.md#logged-fields-per-run) on each run.

Modules for `efficiency`, `failure_fingerprint`, `run_cost_usd`, and `cost_efficiency` still exist under `harnesslab/eval/` but are **not** wired into the published `EVALUATORS` list. HTML Pareto charts estimate cost from run tokens locally instead of publishing those feedback keys.

---

## The five evaluators

| # | Evaluator | Score range | What it measures |
|---|-----------|-------------|------------------|
| 1 | **`task_pass`** | 0.0–1.0 | Did the agent produce the **correct task outcome**? |
| 2 | **`graph_trajectory`** | 0.0–1.0 | Did the agent follow the **expected graph path**? |
| 3 | **`coordination_pass`** | 0.0–1.0 | Did required **stages** appear in order (multi-node topologies)? |
| 4 | **`error_recovery`** | 0.0–1.0 | Did the agent stay within the **acceptable tool-error budget**? |
| 5 | **`ttft_seconds`** | seconds | Wall-clock **time to first token** (lower is better) |

---

## 1. `task_pass` — outcome correctness

**Question:** Did the agent classify correctly and draft a reply that includes required terms?

**Reads from run:** `classification`, `details.final_reply` (via `run_output_field`)

**Compares to dataset:** `classification`, `required_reply_terms`

**Scoring:**
- 50% weight on category match (reference `classification` substring in run `classification`)
- 50% weight on required reply terms (`required_reply_terms` found in reply text)
- Partial credit when only some terms match

**Why keep it:** This is the primary win/loss signal. A harness that finishes quickly but picks the wrong category should lose here.

**Example comment:** `category_ok=True, terms_ok=False, missing_terms=['database'], score=0.50`

---

## 2. `graph_trajectory` — behavioral path

**Question:** Did the agent traverse the expected LangGraph node sequence (e.g. `agent` → `tools` → `agent`)?

**Reads from run:** `details.graph_trajectory` (via `run_output_field`)

**Compares to dataset:** `expected_nodes`

**Scoring:**
- Full credit when `expected_nodes` appears as a subsequence in the actual node list
- Partial credit (`progress`) when only a prefix matches
- Skipped when the task has no `expected_nodes`

**Why keep it:** Explains *why* one harness beat another. Trim middleware changes paths; retry middleware adds extra `agent`↔`tools` loops. Category alone cannot show that.

**Example comment:** `matched=False, progress=0.75, actual=['agent', 'tools', 'agent', 'tools']`

Specialist topologies emit named nodes such as `gather`, `supervisor` workers (`metrics_worker`, …), `planner`, and `verify`. Set `expected_nodes` accordingly when comparing `--by graphs`.

---

## 3. `coordination_pass` — required stages

**Question:** Did the run traverse required coordination stages in order?

**Reads from run:** `details.graph_trajectory`

**Compares to dataset:** `required_stages` (preferred) or falls back to `expected_nodes`

**Scoring:**
- Full credit when required stages appear as a subsequence of visited nodes
- Partial credit via the same progress metric as `graph_trajectory`
- Skipped (1.0) when the task defines neither field

**Why keep it:** Separates “did the multi-node graph coordinate?” from generic path matching. Useful for supervisor / pipeline / plan-execute arms.

**Example comment:** `progress=1.00, required=['intake', 'metrics_worker', 'finalize'], actual=[...]`

---

## 4. `error_recovery` — flaky-tool resilience

**Question:** Did the agent accumulate no more tool errors than the task allows?

**Reads from run:** `error_count`

**Compares to dataset:** `max_acceptable_errors`

**Scoring:**
- 1.0 when `error_count <= max_acceptable_errors`
- 0.0 when errors exceed the budget
- Defaults to zero tolerance when `max_acceptable_errors` is omitted

**Why keep it:** Stress tasks (`R-001`, `I-101`) inject flaky tools. This is where the **retry** harness should outperform **minimal**.

**Example comment:** `error_count=1, max_acceptable=2`

---

## 5. `ttft_seconds` — time to first token

**Question:** How long until the first streamed model token?

**Reads from run:** `details.ttft_seconds` (preferred), else `first_token_time` / root `new_token` events

**Scoring:** Wall-clock seconds (lower is better). `0.0` with comment `ttft_unavailable` when timing is missing.

**Why keep it:** LangSmith’s built-in **Time to First Token** column stays blank for agent `evaluate` Target rows even when `first_token_time` is set. This feedback key is the user-visible TTFT cell in the experiment table. Prefer this column over the native TTFT header.

**Example comment:** `ttft_seconds=2.164`

---

## Looking at LangSmith

- Open the **newest** experiment after a compare. Older experiments keep whatever feedback keys they were published with forever (including dropped keys like `efficiency`, `failure_fingerprint`, `run_cost_usd`).
- Ignore the built-in **Time to First Token** column when it is blank; use feedback **`ttft_seconds`** instead.
