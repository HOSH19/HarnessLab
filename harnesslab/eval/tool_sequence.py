"""Tool call sequence evaluator for LangSmith experiments.

Scores whether observed tool invocations contain expected tools
in order. Uses message and trajectory data attached to run outputs.
"""

from langsmith.schemas import Example, Run

from harnesslab.eval.trajectory import _is_subsequence
from harnesslab.graph.extract import extract_tool_names_from_outputs


def tool_sequence(run: Run, example: Example) -> dict:
    """Score tool invocation order against expected tool subsequence.

    Args:
        run: LangSmith run containing messages or graph_trajectory outputs.
        example: Dataset example with optional expected_tools reference.

    Returns:
        Dict with score and comment describing tool sequence match.
    """
    reference = example.outputs or {}
    expected_tools = reference.get("expected_tools")
    if not expected_tools:
        return {
            "key": "tool_sequence",
            "score": 1.0,
            "comment": "no expected_tools",
        }

    outputs = run.outputs or {}
    actual_tools = extract_tool_names_from_outputs(outputs)
    matched = _is_subsequence(list(expected_tools), actual_tools)

    return {
        "key": "tool_sequence",
        "score": 1.0 if matched else 0.0,
        "comment": f"expected={list(expected_tools)}, actual={actual_tools}",
    }
