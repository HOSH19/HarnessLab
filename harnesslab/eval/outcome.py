"""Task pass/fail evaluator for ticket triage outputs.

Checks classification and reply content against task fixtures.
Does not call LLMs or access LangSmith directly.
"""

from langsmith.schemas import Example, Run


def task_pass(run: Run, example: Example) -> dict:
    """Score whether the agent produced a correct triage result.

    Args:
        run: LangSmith run with agent outputs.
        example: Dataset example with expected fields.

    Returns:
        Dict with score key (1.0 pass, 0.0 fail) and comment.
    """
    outputs = run.outputs or {}
    reference = example.outputs or example.inputs or {}
    expected_category = reference.get("expected_category", "")
    required_terms = reference.get("required_reply_terms", [])

    classification = str(outputs.get("classification", "")).lower()
    reply = str(outputs.get("final_reply", "")).lower()

    category_ok = expected_category.lower() in classification if expected_category else True
    terms_ok = all(term.lower() in reply for term in required_terms)

    passed = category_ok and terms_ok
    return {
        "key": "task_pass",
        "score": 1.0 if passed else 0.0,
        "comment": f"category_ok={category_ok}, terms_ok={terms_ok}",
    }
