# Task Ablation Analysis — gpt-4.1-nano + minimal

**Generated:** 2026-08-28
**Run:** `2026-08-28T23-36-47_gpt-4-1-nano`
**Dataset:** `task_ablation`
**Model:** `gpt-4.1-nano` | **Harness:** `minimal`
**Tasks:** T-011 through T-019 (9 stress tasks)

---

## Executive summary

| Metric | Average |
|---|---:|
| **task_pass** | **0.78** |
| **tool_sequence** | **0.64** |
| **graph_trajectory** | **0.83** |
| **failure_fingerprint** | **1.00** |
| **efficiency** | **1.00** |
| **error_recovery** | **1.00** |
| **step_count** | **1.00** |

- **Full passes (task_pass=1.0):** 4 — T-011, T-013, T-014, T-015
- **Partial credit:** 4 — T-012 (0.75), T-016 (0.67), T-017 (0.88), T-018 (0.75)
- **Hard failures (task_pass=0.0):** 1 — T-019

---

## Per-task results

| Ticket | output | task_pass | tool_sequence | graph_trajectory | failure |
|---|---|---:|---:|---:|---|
| **T-011** | `technical` | 1.00 | 1.00 | 0.75 | SUCCESS |
| **T-012** | `billing` | 0.75 | 0.25 | 0.88 | SUCCESS |
| **T-013** | `billing` | 1.00 | 1.00 | 1.00 | SUCCESS |
| **T-014** | `technical` | 1.00 | 0.20 | 0.90 | SUCCESS |
| **T-015** | `technical` | 1.00 | 1.00 | 0.75 | SUCCESS |
| **T-016** | `technical` | 0.67 | 0.33 | 0.75 | SUCCESS |
| **T-017** | `account` | 0.88 | 1.00 | 1.00 | SUCCESS |
| **T-018** | `technical` | 0.75 | 0.71 | 0.56 | SUCCESS |
| **T-019** | `technical` | 0.00 | 0.25 | 0.88 | SUCCESS |

---

## Per-task detail

### T-011 — Flaky read_ticket (2 failures)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Hello,  Thank you for reaching out regarding the database connection timeout errors. We understand the impact this can have on your operations.  Our technical team has been notified and is investigati |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'check_sla', 'classify', 'draft_reply']` |
| graph_trajectory | 0.75 — `matched=False, progress=0.75, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3406, tokens=0, steps=9, graph_steps=9` |

### T-012 — 14-turn conversation context recall

| Field | Value |
|---|---|
| Classification (output) | `billing` |
| final_reply | Your refund request for order #9912 has been received and is being processed under our billing policy. You will receive a confirmation once the refund is completed. If you have any further questions,  |
| task_pass | 0.75 — `category_ok=True, terms_ok=False, terms_score=0.50, missing_terms=['7788', 'annual'], score=0.75` |
| tool_sequence | 0.25 — `matched=False, progress=0.25, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'check_sla', 'classify', 'draft_reply']` |
| graph_trajectory | 0.88 — `matched=False, progress=0.88, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=2680, tokens=0, steps=7, graph_steps=7` |

### T-013 — Merged-account billing dispute

| Field | Value |
|---|---|
| Classification (output) | `billing` |
| final_reply | Thank you for reaching out regarding the billing issue after your account merge. We will review the charge and work to resolve this dispute promptly. Please allow us some time to investigate and get b |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 1.00 — `matched=True, progress=1.00, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3914, tokens=0, steps=9, graph_steps=9` |

### T-014 — Dual KB search required

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Hello,  Thank you for reaching out regarding the webhook failures and database migration issues. Based on your description, it appears to be related to technical problems following your recent databas |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 0.20 — `matched=False, progress=0.20, expected=['read_ticket', 'search_kb', 'search_kb', 'classify', 'draft_reply'], actual=['search_kb', 'search_kb', 'read_ticket', 'classify', 'draft_reply']` |
| graph_trajectory | 0.90 — `matched=False, progress=0.90, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3682, tokens=0, steps=9, graph_steps=9` |

### T-015 — Flaky search_kb (2 failures)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Thank you for reaching out about the SSL certificate issue. It appears that your certificate has expired, which is causing the error when accessing your dashboard. Please follow our SSL renewal proced |
| task_pass | 1.00 — `category_ok=True, terms_ok=True, terms_score=1.00, missing_terms=[], score=1.00` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'check_sla', 'classify', 'draft_reply']` |
| graph_trajectory | 0.75 — `matched=False, progress=0.75, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3829, tokens=0, steps=9, graph_steps=9` |

### T-016 — Priority SLA + escalate

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Hello,  We acknowledge the critical nature of the outage affecting your production API. Our engineering on-call team has been escalated to address this priority issue immediately. We are working dilig |
| task_pass | 0.67 — `category_ok=True, terms_ok=False, terms_score=0.33, missing_terms=['sla', '503'], score=0.67` |
| tool_sequence | 0.33 — `matched=False, progress=0.33, expected=['read_ticket', 'check_sla', 'search_kb', 'classify', 'escalate_ticket', 'draft_reply'], actual=['read_ticket', 'check_sla', 'escalate_ticket', 'classify', 'draft_reply']` |
| graph_trajectory | 0.75 — `matched=False, progress=0.75, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3148, tokens=0, steps=9, graph_steps=9` |

### T-017 — Category trap (billing → account)

| Field | Value |
|---|---|
| Classification (output) | `account` |
| final_reply | Thank you for reaching out. It appears that your email verification is pending, which is preventing access to your invoices. Please ensure that you have completed the email verification process for yo |
| task_pass | 0.88 — `category_ok=True, terms_ok=False, terms_score=0.75, missing_terms=['8823'], score=0.88` |
| tool_sequence | 1.00 — `matched=True, progress=1.00, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 1.00 — `matched=True, progress=1.00, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3159, tokens=0, steps=9, graph_steps=9` |

### T-018 — Tool budget + flaky search_kb/escalate

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | The ticket has been classified as technical. Based on the urgency and the KB guidance, I will escalate this to engineering on-call for immediate attention to the API outage and webhook delivery issues |
| task_pass | 0.75 — `category_ok=True, terms_ok=False, terms_score=0.50, missing_terms=['sla', '503'], score=0.75` |
| tool_sequence | 0.71 — `matched=False, progress=0.71, expected=['read_ticket', 'check_sla', 'search_kb', 'search_kb', 'classify', 'escalate_ticket', 'draft_reply'], actual=['read_ticket', 'check_sla', 'search_kb', 'search_kb', 'classify', 'draft_reply']` |
| graph_trajectory | 0.56 — `matched=False, progress=0.56, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=3720, tokens=0, steps=9, graph_steps=9` |

### T-019 — Adversarial prompt (sync vs billing)

| Field | Value |
|---|---|
| Classification (output) | `technical` |
| final_reply | Thank you for reaching out about the sync error with code 504. This issue often relates to cache synchronization problems. Please try clearing your desktop application's cache and restarting the app.  |
| task_pass | 0.00 — `category_ok=False, terms_ok=False, terms_score=0.00, missing_terms=['duplicate', 'refund', '4455', 'charge'], score=0.00` |
| tool_sequence | 0.25 — `matched=False, progress=0.25, expected=['read_ticket', 'search_kb', 'classify', 'draft_reply'], actual=['read_ticket', 'classify', 'draft_reply']` |
| graph_trajectory | 0.88 — `matched=False, progress=0.88, actual=['__start__', 'agent', 'tools', 'agent', 'tools', 'agent', 'tools', 'agent']` |
| failure_fingerprint | SUCCESS |
| efficiency | `latency_ms=4222, tokens=0, steps=7, graph_steps=7` |

---

## Task difficulty ranking (by task_pass)

1. **T-011** — 1.00 (Flaky read_ticket (2 failures))
2. **T-013** — 1.00 (Merged-account billing dispute)
3. **T-014** — 1.00 (Dual KB search required)
4. **T-015** — 1.00 (Flaky search_kb (2 failures))
5. **T-017** — 0.88 (Category trap (billing → account))
6. **T-012** — 0.75 (14-turn conversation context recall)
7. **T-018** — 0.75 (Tool budget + flaky search_kb/escalate)
8. **T-016** — 0.67 (Priority SLA + escalate)
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
  "timestamp": "2026-08-28T23:36:47.234895+00:00"
}
```

## Summary scores

```json
{
  "gpt-4.1-nano": {
    "efficiency": 1.0,
    "error_recovery": 1.0,
    "failure_fingerprint": 1.0,
    "graph_trajectory": 0.8291666666666667,
    "step_count": 1.0,
    "task_pass": 0.7833333333333333,
    "tool_sequence": 0.6377777777777778
  }
}
```

