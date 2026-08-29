# HarnessLab Evaluators

HarnessLab scores every agent run on **five evaluators**. Together they answer: *did harness X beat harness Y on task Z, and why?*

These are **feedback scores** uploaded to LangSmith (or stored in local JSON). They are separate from the [five logged output fields](HARNESSES.md#logged-fields-per-run) on each run.

---

## The five evaluators

| # | Evaluator | Score range | What it measures |
|---|-----------|-------------|------------------|
| 1 | **`task_pass`** | 0.0–1.0 | Did the agent produce the **correct task outcome**? |
| 2 | **`graph_trajectory`** | 0.0–1.0 | Did the agent follow the **expected graph path**? |
| 3 | **`error_recovery`** | 0.0–1.0 | Did the agent stay within the **acceptable tool-error budget**? |
| 4 | **`efficiency`** | 0.0–1.0 | Was the run **fast and lean** enough? |
| 5 | **`failure_fingerprint`** | 0.0–1.0 | What **failure category** best describes the run? |

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

---

## 3. `error_recovery` — flaky-tool resilience

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

## 4. `efficiency` — cost and speed

**Question:** Was the run reasonably fast, token-efficient, and within step budget?

**Reads from run:** LangSmith timing/token metadata, `graph_trajectory` step count

**Compares to dataset:** `expected_max_steps`

**Scoring:** Starts at 1.0, then penalizes:
- High latency (>6s)
- High token usage (>1,500)
- Too many agent/tool steps vs `expected_max_steps`

**Why keep it:** Harness A/B is not only about correctness. A harness that passes every task but burns 3× latency or tokens is not a win in production.

**Example comment:** `latency_ms=4200, tokens=890, steps=8, graph_steps=8`

---

## 5. `failure_fingerprint` — failure taxonomy

**Question:** When something goes wrong, *what kind* of failure is it?

**Reads from run:** `classification`, `details.final_reply`, `run.error`, latency

**Compares to dataset:** (none — rule-based classification)

**Categories:** `SUCCESS`, `TIMEOUT`, `TOOL_ERROR`, `PARSE_ERROR`, `WRONG_ANSWER`, `MAX_TURNS`

**Scoring:** 1.0 for `SUCCESS`, 0.0 for failure categories (stored in comment)

**Why keep it:** Speeds up debugging across many tasks. A column of `TOOL_ERROR` vs `WRONG_ANSWER` tells you whether to tune retries vs prompts.

**Example comment:** `WRONG_ANSWER`
