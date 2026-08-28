"""HTML report generation tests."""

from harnesslab.report.html import render_comparison_html


class _FakeEvalResult:
    def __init__(self, key: str, score: float, comment: str = ""):
        self.key = key
        self.score = score
        self.comment = comment


class _FakeExample:
    def __init__(self, inputs: dict):
        self.inputs = inputs


class _FakeRow:
    def __init__(self, ticket_id: str, scores: dict[str, float], comments: dict[str, str] | None = None):
        self.example = _FakeExample({"ticket_id": ticket_id, "prompt": f"Triage {ticket_id}"})
        comments = comments or {}
        self.evaluation_results = {
            "results": [
                _FakeEvalResult(key, score, comments.get(key, ""))
                for key, score in scores.items()
            ]
        }


def test_render_comparison_html_includes_harness_names() -> None:
    """Report HTML contains harness rows."""
    html = render_comparison_html({"minimal": [], "with_retry": []})
    assert "minimal" in html
    assert "with_retry" in html
    assert "task_pass" in html
    assert "tool_sequence" in html
    assert "Per-task breakdown" in html


def test_render_comparison_html_supports_model_dimension() -> None:
    """Report HTML uses the requested comparison dimension label."""
    html = render_comparison_html({"gpt-4.1-nano": []}, dimension="Model")
    assert "Model Comparison" in html
    assert "gpt-4.1-nano" in html


def test_render_comparison_html_includes_per_task_rows() -> None:
    """Per-task section lists arm, task, and parsed efficiency metrics."""
    row = _FakeRow(
        "T-011",
        {
            "task_pass": 1.0,
            "tool_sequence": 1.0,
            "error_recovery": 1.0,
            "step_count": 0.8,
            "efficiency": 0.9,
        },
        {"efficiency": "latency_ms=1200, tokens=500, steps=6"},
    )
    html = render_comparison_html({"minimal": [row]})
    assert "T-011" in html
    assert "1200" in html
    assert "500" in html
    assert "0.80" in html
