"""Local experiment runner tests."""

from unittest.mock import MagicMock

from harnesslab.experiments.local_runner import run_local_experiment
from harnesslab.experiments.runner import EVALUATORS
from langsmith.schemas import Example


def _example(ticket_id: str = "I-101") -> Example:
    return Example(
        id="00000000-0000-4000-8000-000000000001",
        dataset_id="00000000-0000-4000-8000-000000000099",
        inputs={"prompt": "test", "ticket_id": ticket_id},
        outputs={
            "classification": "infrastructure",
            "required_reply_terms": ["payments-api"],
            "expected_nodes": ["agent", "tools", "agent"],
            "max_acceptable_errors": 0,
        },
    )


def test_run_local_experiment_returns_scored_rows() -> None:
    """Local runner produces rows with evaluator scores without LangSmith evaluate."""
    target = MagicMock(
        return_value={
            "classification": "infrastructure",
            "error_count": 0,
            "total_tokens": 120,
            "model": "gpt-4.1-nano",
            "details": {
                "final_reply": "payments-api db pool exhaustion",
                "graph_trajectory": {
                    "steps": [["agent", "tools", "agent"]],
                    "results": [],
                    "inputs": [],
                },
            },
        }
    )

    results = run_local_experiment(
        target,
        [_example()],
        EVALUATORS,
        experiment_prefix="minimal",
        metadata={"harness": {"name": "minimal"}},
    )

    assert len(results) == 1
    row = results[0]
    scores = {item.key: item.score for item in row["evaluation_results"]["results"]}
    assert scores["task_pass"] > 0
    assert scores["run_cost_usd"] > 0
    assert row["run"].outputs["total_tokens"] == 120
