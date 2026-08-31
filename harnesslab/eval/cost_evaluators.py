"""Cost-related LangSmith evaluators."""

from langsmith.schemas import Example, Run

from harnesslab.eval.cost import estimate_run_cost_usd
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.run_metrics import run_total_tokens


def run_cost_usd(run: Run, example: Example) -> dict:
    """Publish estimated USD cost per run (lower is better; score is raw dollars)."""
    _ = example
    cost = estimate_run_cost_usd(run)
    tokens = run_total_tokens(run)
    return {
        "key": "run_cost_usd",
        "score": cost,
        "comment": f"cost_usd={cost:.6f}, tokens={tokens}",
    }


def cost_efficiency(run: Run, example: Example) -> dict:
    """Publish task_pass per USD — higher means better value for money."""
    cost = max(estimate_run_cost_usd(run), 1e-6)
    pass_score = float(task_pass(run, example)["score"])
    ratio = round(pass_score / cost, 2)
    return {
        "key": "cost_efficiency",
        "score": ratio,
        "comment": f"task_pass={pass_score:.2f}, cost_usd={cost:.6f}, ratio={ratio:.2f}",
    }
