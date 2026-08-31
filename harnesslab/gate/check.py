"""Harness regression gate checks against benchmark baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harnesslab.gate.significance import bootstrap_mean_delta, collect_task_scores


LOWER_IS_BETTER = frozenset({"run_cost_usd"})


@dataclass
class GateResult:
    """Outcome of a harness regression gate check."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)


def check_regression(
    *,
    baseline: dict[str, Any],
    comparisons: dict[str, list],
    summary_keys: list[str],
    max_regression: float = 0.05,
    blocking_evaluators: list[str] | None = None,
) -> GateResult:
    """Compare current compare results against a stored baseline."""
    blocking = blocking_evaluators or ["task_pass", "error_recovery"]
    baseline_arms = baseline.get("arms", {})
    failures: list[str] = []
    details: list[dict[str, Any]] = []

    for arm_name, rows in comparisons.items():
        if arm_name not in baseline_arms:
            failures.append(f"Missing baseline for arm: {arm_name}")
            continue

        arm_base = baseline_arms[arm_name]
        for key in summary_keys:
            if key not in blocking and key not in arm_base:
                continue

            base_avg = float(arm_base.get(key, 0.0))
            current_scores = collect_task_scores(rows, key)
            baseline_scores = [
                float(task_scores.get(key, base_avg))
                for task_scores in arm_base.get("per_task", {}).values()
            ] or [base_avg]

            mean_delta, lower, upper = bootstrap_mean_delta(baseline_scores, current_scores)
            if key in LOWER_IS_BETTER:
                mean_delta = -mean_delta
                lower, upper = -upper, -lower

            detail = {
                "arm": arm_name,
                "evaluator": key,
                "baseline": base_avg,
                "mean_delta": mean_delta,
                "ci_lower": lower,
                "ci_upper": upper,
            }
            details.append(detail)

            if key in blocking and upper < -max_regression:
                failures.append(
                    f"{arm_name}/{key} regressed: delta={mean_delta:.4f}, ci_upper={upper:.4f}"
                )

    return GateResult(passed=not failures, failures=failures, details=details)
