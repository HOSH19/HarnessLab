"""Tool call sequence evaluator for Langfuse experiments.

Scores whether observed tool invocations contain expected tools
in order. Uses message and trajectory data attached to run outputs.
"""

from harnesslab.eval.sequence import subsequence_progress
from harnesslab.graph.extract import extract_tool_names_from_outputs


def tool_sequence(run, example) -> dict:
    """Score tool invocation order against expected tool subsequence.

    Args:
        run: Run-like object containing messages or graph_trajectory outputs.
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
    score = subsequence_progress(list(expected_tools), actual_tools)
    matched = score == 1.0

    return {
        "key": "tool_sequence",
        "score": round(score, 2),
        "comment": (
            f"matched={matched}, progress={score:.2f}, "
            f"expected={list(expected_tools)}, actual={actual_tools}"
        ),
    }
