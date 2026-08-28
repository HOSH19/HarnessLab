"""Local experiment result persistence tests."""

import json
from pathlib import Path

from harnesslab.experiments.store import (
    save_compare_run,
    save_experiment_run,
    serialize_result_row,
)


class _FakeEvalResult:
    def __init__(self, key: str, score: float, comment: str = ""):
        self.key = key
        self.score = score
        self.comment = comment


class _FakeExample:
    def __init__(self, inputs: dict, example_id: str = "ex-001"):
        self.inputs = inputs
        self.id = example_id


class _FakeRun:
    def __init__(self, run_id: str = "run-001"):
        self.id = run_id


class _FakeRow:
    def __init__(
        self,
        ticket_id: str,
        scores: dict[str, float],
        comments: dict[str, str] | None = None,
        *,
        example_id: str = "ex-001",
        run_id: str = "run-001",
    ):
        self.example = _FakeExample(
            {"ticket_id": ticket_id, "prompt": f"Triage {ticket_id}"},
            example_id=example_id,
        )
        self.run = _FakeRun(run_id=run_id)
        self.outputs = {"classification": "billing", "final_reply": "Done"}
        comments = comments or {}
        self.evaluation_results = {
            "results": [
                _FakeEvalResult(key, score, comments.get(key, ""))
                for key, score in scores.items()
            ]
        }


def test_serialize_result_row_includes_core_fields() -> None:
    """Serialized rows include inputs, outputs, scores, and identifiers."""
    row = _FakeRow(
        "T-001",
        {"task_pass": 1.0, "efficiency": 0.9},
        {"efficiency": "latency_ms=1200, tokens=500, steps=6"},
        example_id="ex-123",
        run_id="run-456",
    )

    payload = serialize_result_row(row)

    assert payload["example_id"] == "ex-123"
    assert payload["run_id"] == "run-456"
    assert payload["inputs"]["ticket_id"] == "T-001"
    assert payload["outputs"]["classification"] == "billing"
    assert payload["evaluation_results"]["task_pass"]["score"] == 1.0
    assert "latency_ms=1200" in payload["evaluation_results"]["efficiency"]["comment"]


def test_serialize_result_row_reads_nested_run_outputs() -> None:
    """Serialized rows fall back to nested run.outputs when row.outputs is empty."""
    row = _FakeRow("T-018", {"task_pass": 1.0})
    row.outputs = {}
    row.run.outputs = {
        "output": "technical",
        "classification": "technical",
        "details": {"final_reply": "Escalated outage"},
    }

    payload = serialize_result_row(row)

    assert payload["outputs"]["classification"] == "technical"
    assert payload["outputs"]["details"]["final_reply"] == "Escalated outage"
    assert payload["outputs"]["output"] == "technical"


def test_save_experiment_run_roundtrip(tmp_path: Path) -> None:
    """Single-harness runs write manifest, results, and summary JSON."""
    row = _FakeRow("T-001", {"task_pass": 1.0, "tool_sequence": 0.5})
    metadata = {"langsmith_mode": False, "model": "gpt-4o-mini"}

    run_dir = save_experiment_run("minimal", [row], out_dir=tmp_path, metadata=metadata)

    assert run_dir.name.endswith("_minimal")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    results = json.loads((run_dir / "minimal.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())

    assert manifest["arms"] == ["minimal"]
    assert manifest["task_count"] == 1
    assert manifest["langsmith_mode"] is False
    assert manifest["model"] == "gpt-4o-mini"
    assert len(results) == 1
    assert results[0]["inputs"]["ticket_id"] == "T-001"
    assert summary["minimal"]["task_pass"] == 1.0
    assert summary["minimal"]["tool_sequence"] == 0.5


def test_save_compare_run_roundtrip(tmp_path: Path) -> None:
    """Compare runs write one JSON file per harness plus summary."""
    comparisons = {
        "minimal": [_FakeRow("T-001", {"task_pass": 1.0})],
        "retry": [_FakeRow("T-001", {"task_pass": 0.5})],
    }

    run_dir = save_compare_run(
        comparisons,
        out_dir=tmp_path,
        metadata={"langsmith_mode": True, "compare_by": "harness", "harnesses": ["minimal", "retry"]},
    )

    assert run_dir.name.endswith("_harness")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    minimal = json.loads((run_dir / "minimal.json").read_text())
    retry = json.loads((run_dir / "retry.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())

    assert manifest["arms"] == ["minimal", "retry"]
    assert manifest["task_count"] == 1
    assert manifest["langsmith_mode"] is True
    assert len(minimal) == 1
    assert len(retry) == 1
    assert summary["minimal"]["task_pass"] == 1.0
    assert summary["retry"]["task_pass"] == 0.5
