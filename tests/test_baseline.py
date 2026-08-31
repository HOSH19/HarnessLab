"""Benchmark baseline export tests."""

import json
from pathlib import Path

from harnesslab.gate.baseline import build_baseline, write_baseline


class _FakeEval:
    def __init__(self, key, score):
        self.key = key
        self.score = score


class _FakeExample:
    def __init__(self, ticket_id: str):
        self.inputs = {"ticket_id": ticket_id}


class _FakeRow:
    def __init__(self, ticket_id: str, scores: dict[str, float]):
        self.example = _FakeExample(ticket_id)
        self.evaluation_results = {"results": [_FakeEval(k, v) for k, v in scores.items()]}


def test_build_and_write_baseline(tmp_path: Path) -> None:
    """Baseline export captures per-arm averages and per-task scores."""
    comparisons = {
        "retry": [_FakeRow("I-101", {"task_pass": 1.0, "run_cost_usd": 0.001})],
    }
    payload = build_baseline(
        example="examples/incident_manager",
        comparisons=comparisons,
        summary_keys=["task_pass", "run_cost_usd"],
    )
    path = write_baseline(tmp_path / "baseline.json", payload)
    loaded = json.loads(path.read_text())
    assert loaded["example"] == "examples/incident_manager"
    assert loaded["arms"]["retry"]["task_pass"] == 1.0
    assert loaded["arms"]["retry"]["per_task"]["I-101"]["task_pass"] == 1.0
