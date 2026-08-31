"""Bootstrap significance helpers for harness regression gates."""

from __future__ import annotations

import random
from typing import Any


def bootstrap_mean_delta(
    baseline_scores: list[float],
    current_scores: list[float],
    *,
    samples: int = 1000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Return mean delta and 95% CI for current - baseline via bootstrap."""
    if not baseline_scores or not current_scores:
        return 0.0, 0.0, 0.0

    rng = random.Random(seed)
    deltas: list[float] = []
    for _ in range(samples):
        b = [baseline_scores[rng.randrange(len(baseline_scores))] for _ in baseline_scores]
        c = [current_scores[rng.randrange(len(current_scores))] for _ in current_scores]
        deltas.append((sum(c) / len(c)) - (sum(b) / len(b)))

    deltas.sort()
    mean_delta = sum(current_scores) / len(current_scores) - sum(baseline_scores) / len(baseline_scores)
    lower = deltas[int(0.025 * len(deltas))]
    upper = deltas[int(0.975 * len(deltas)) - 1]
    return round(mean_delta, 4), round(lower, 4), round(upper, 4)


def collect_task_scores(rows: list[Any], key: str) -> list[float]:
    """Collect per-task evaluator scores from compare rows."""
    from harnesslab.report.results import score_for_key

    scores: list[float] = []
    for row in rows:
        score = score_for_key(row, key)
        if score is not None:
            scores.append(float(score))
    return scores
