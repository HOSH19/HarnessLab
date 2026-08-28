# Task Ablation Analysis — gpt-4.1-nano + minimal

**Generated:** 2026-08-28
**Run:** `2026-08-28T23-26-35_gpt-4-1-nano`
**Dataset:** `task_ablation`
**Model:** `gpt-4.1-nano` | **Harness:** `minimal`
**Tasks:** T-011 through T-019 (9 stress tasks)

---

## Executive summary

| Metric | Average |
|---|---:|
| **task_pass** | **0.47** |
| **tool_sequence** | **0.56** |
| **graph_trajectory** | **0.71** |
| **failure_fingerprint** | **0.56** |
| **efficiency** | **1.00** |
| **error_recovery** | **1.00** |
| **step_count** | **1.00** |

- **Full passes (task_pass=1.0):** 2 — T-011, T-015
- **Partial credit:** 3 — T-013 (0.83), T-014 (0.50), T-017 (0.88)
- **Hard failures (task_pass=0.0):** 4 — T-012, T-016, T-018, T-019

---

## Per-task results

| Ticket | output | task_pass | tool_sequence | graph_trajectory | failure |
|---|---|---:|---:|---:|---|
| **T-011** | `technical` | 1.00 | 1.00 | 0.92 | SUCCESS |
| **T-012** | `(empty)` | 0.00 | 0.25 | 0.38 | WRONG_ANSWER |
| **T-013** | `billing` | 0.83 | 1.00 | 1.00 | SUCCESS |
| **T-014** | `technical` | 0.50 | 0.20 | 0.70 | WRONG_ANSWER |
| **T-015** | `technical` | 1.00 | 1.00 | 0.75 | SUCCESS |
| **T-016** | `(empty)` | 0.00 | 0.33 | 0.42 | WRONG_ANSWER |
| **T-017** | `account` | 0.88 | 1.00 | 1.00 | SUCCESS |
| **T-018** | `(empty)` | 0.00 | 0.00 | 0.31 | WRONG_ANSWER |
| **T-019** | `technical` | 0.00 | 0.25 | 0.88 | SUCCESS |

---

## Per-task detail

### T-011 — Flaky read_ticket (2 failures)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Hello,  Thank you for reaching out regarding the database connection timeout errors. We understand the impact this can have on your production environment.  Our technical team is currently investigati |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'check_sla', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 0.92 — `matched=False, progress=0.92, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=6115, tokens=0, steps=11, graph_steps=11` |

### T-012 — 14-turn conversation context recall

| Field | Value |
|---|---|
| Classification (output) | `(empty)` |
| final_reply | (empty) |
| task_pass | 0.00 — `category_ok=False, terms_ok=False, terms_score=0.00, missing_terms=['7788', '9912', 'annual', 'refund'], score=0.00` |
| tool_sequence | 0.25 — `matched=False, progress=0.25, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'check_sla']` |
| graph_trajectory | 0.38 — `matched=False, progress=0.38, actual=['__start__', 'agent', 'tools', 'agent']` |
| failure_fingerprint | WRONG_ANSWER |
| efficiency | `latency_ms=2030, tokens=0, steps=3, graph_steps=3` |

### T-013 — Merged-account billing dispute

| Field | Value |
|---|---|
| Classification (output) | `billing` |
| final_reply | Thank you for reaching out regarding the billing issue after your account merge. We understand the importance of resolving this promptly. We will review your account details and billing history to cor |
| task_pass | 0.83 — `category_ok=True, terms_ok=False, terms_score=0.67, missing_terms=['dispute'], score=0.83` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 1.00 — `matched=True, progress=1.00, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=4544, tokens=0, steps=9, graph_steps=9` |

### T-014 — Dual KB search required

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | (empty) |
| task_pass | 0.50 — `category_ok=True, terms_ok=False, terms_score=0.00, missing_terms=['webhook', 'database'], score=0.50` |
| tool_sequence | 0.20 — `matched=False, progress=0.20, expected=['read_ticket', 'search_kb', 'search_kb', 'classify', 'draft_reply'], actual=['search_kb', 'search_kb', 'read_ticket', 'classify']` |
| graph_trajectory | 0.70 — `matched=False, progress=0.70, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | WRONG_ANSWER |
| efficiency | `latency_ms=3185, tokens=0, steps=7, graph_steps=7` |

### T-015 — Flaky search_kb (2 failures)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Hello,  Thank you for reaching out. It appears that your SSL certificate has expired, which is causing the error when accessing your dashboard. Please renew your SSL certificate to resolve this issue. |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'check_sla', 'classify', 'draft_reply']` |
| graph_trajectory | 0.75 — `matched=False, progress=0.75, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=4580, tokens=0, steps=9, graph_steps=9` |

### T-016 — Priority SLA + escalate

| Field | Value |
|---|---|
| Classification (output) | `(empty)` |
| final_reply | (empty) |
| task_pass | 0.00 — `category_ok=False, terms_ok=False, terms_score=0.00, missing_terms=['sla', 'escalat', '503'], score=0.00` |
| tool_sequence | 0.33 — `matched=False, progress=0.33, expected=['read_ticket', 'check_sla', 'search_kb', 'classify', 'escalate_ticket', 'draft_reply'], actual=['read_ticket', 'check_sla', 'escalate_ticket']` |
| graph_trajectory | 0.42 — `matched=False, progress=0.42, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | WRONG_ANSWER |
| efficiency | `latency_ms=3162, tokens=0, steps=5, graph_steps=5` |

### T-017 — Category trap (billing → account)

| Field | Value |
|---|---|
| Classification (output) | `account` |
| final_reply | Thank you for reaching out. It appears that your email verification is pending, which is preventing access to your invoices. Please ensure that you have completed the email verification process for yo |
| task_pass | 0.88 — `category_ok=True, terms_ok=False, terms_score=0.75, missing_terms=['8823'], score=0.88` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 1.00 — `matched=True, progress=1.00, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=5046, tokens=0, steps=9, graph_steps=9` |

### T-018 — Tool budget + flaky search_kb/escalate

| Field | Value |
|---|---|
| Classification (output) | `(empty)` |
| final_reply | (empty) |
| task_pass | 0.00 — `category_ok=False, terms_ok=False, terms_score=0.00, missing_terms=['sla', '503', 'webhook', 'escalat'], score=0.00` |
| tool_sequence | 0.00 — `matched=False, progress=0.00, expected=['read_ticket', 'check_sla', 'search_kb', 'search_kb', 'classify', 'escalate_ticket', 'draft_reply'], actual=['check_sla', 'search_kb', 'search_kb', 'escalate_ticket']` |
| graph_trajectory | 0.31 — `matched=False, progress=0.31, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | WRONG_ANSWER |
| efficiency | `latency_ms=2652, tokens=0, steps=5, graph_steps=5` |

### T-019 — Adversarial prompt (sync vs billing)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Thank you for reaching out. Since you're experiencing a desktop sync error with code 504, please try clearing your sync cache and restarting the application. If the issue persists, let us know so we c |
| task_pass | 0.00 — `category_ok=False, terms_ok=False, terms_score=0.00, missing_terms=['duplicate', 'refund', '4455', 'charge'], score=0.00` |
| tool_sequence | 0.25 — `matched=False, progress=0.25, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'classify', 'draft_reply']` |
| graph_trajectory | 0.88 — `matched=False, progress=0.88, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=5407, tokens=0, steps=7, graph_steps=7` |

---

## Task difficulty ranking (by task_pass)

1. **T-011** — 1.00 (Flaky read_ticket (2 failures))
2. **T-015** — 1.00 (Flaky search_kb (2 failures))
3. **T-017** — 0.88 (Category trap (billing → account))
4. **T-013** — 0.83 (Merged-account billing dispute)
5. **T-014** — 0.50 (Dual KB search required)
6. **T-012** — 0.00 (14-turn conversation context recall)
7. **T-016** — 0.00 (Priority SLA + escalate)
8. **T-018** — 0.00 (Tool budget + flaky search_kb/escalate)
9. **T-019** — 0.00 (Adversarial prompt (sync vs billing))

---

## Manifest

```json
{
  "arms": [
    "minimal"
  ],
  "compare_by": "harness",
  "dataset": "task_ablation",
  "example": "/Users/hoshuhan/Documents/UCLA/spring/boredom/harnesslab/examples/ticket_triage",
  "harness": "minimal",
  "harnesses": [
    "gpt-4.1-nano"
  ],
  "langsmith_mode": true,
  "model": "gpt-4.1-nano",
  "models": [
    "gpt-4.1-nano"
  ],
  "task_count": 9,
  "tasks_limit": 9,
  "ticket_id": null,
  "timestamp": "2026-08-28T23:26:35.986645+00:00"
}
```

## Summary scores

```json
{
  "gpt-4.1-nano": {
    "efficiency": 0.9988888888888889,
    "error_recovery": 1.0,
    "failure_fingerprint": 0.5555555555555556,
    "graph_trajectory": 0.7050925925925926,
    "step_count": 1.0,
    "task_pass": 0.4677777777777778,
    "tool_sequence": 0.5588888888888889
  }
}
```

