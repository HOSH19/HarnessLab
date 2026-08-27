"""HTML report generation tests."""

from harnesslab.report.html import render_comparison_html


def test_render_comparison_html_includes_harness_names() -> None:
    """Report HTML contains harness rows."""
    html = render_comparison_html({"minimal": [], "with_retry": []})
    assert "minimal" in html
    assert "with_retry" in html
    assert "task_pass" in html
