"""Cost evaluator tests."""

from harnesslab.eval.cost import estimate_run_cost_usd, resolve_run_model
from harnesslab.eval.cost_evaluators import cost_efficiency, run_cost_usd


class _FakeRun:
    def __init__(self, *, outputs=None, total_tokens=1000, extra=None):
        self.outputs = outputs or {}
        self.total_tokens = total_tokens
        self.extra = extra or {}


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_run_cost_usd_uses_token_pricing() -> None:
    """run_cost_usd scales with token count and model pricing."""
    run = _FakeRun(total_tokens=2000, extra={"metadata": {"model": "gpt-4.1-nano"}})
    result = run_cost_usd(run, _FakeExample({}))
    assert result["key"] == "run_cost_usd"
    assert result["score"] == estimate_run_cost_usd(run)
    assert result["score"] > 0


def test_run_cost_usd_reads_tokens_from_outputs() -> None:
    """Local runs without run.total_tokens still get priced from outputs."""
    run = _FakeRun(
        outputs={
            "details": {"total_tokens": 3000, "model": "gpt-4.1-nano"},
        },
        total_tokens=None,
    )
    result = run_cost_usd(run, _FakeExample({}))
    assert result["score"] > 0
    assert "tokens=3000" in result["comment"]
    assert resolve_run_model(run) == "gpt-4.1-nano"


def test_cost_efficiency_divides_pass_by_cost() -> None:
    """cost_efficiency rewards high task_pass at low cost."""
    run = _FakeRun(
        total_tokens=1000,
        extra={"metadata": {"model": "gpt-4.1-nano"}},
        outputs={
            "classification": "infrastructure",
            "details": {"final_reply": "db pool exhaustion on payments-api"},
        },
    )
    example = _FakeExample(
        {
            "classification": "infrastructure",
            "required_reply_terms": ["payments-api"],
        }
    )
    result = cost_efficiency(run, example)
    assert result["key"] == "cost_efficiency"
    assert result["score"] > 0
