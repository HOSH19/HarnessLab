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
    if required_terms:
        matched_terms = sum(1 for term in required_terms if term.lower() in reply)
        terms_score = matched_terms / len(required_terms)
        terms_ok = matched_terms == len(required_terms)
    else:
        terms_score = 1.0
        terms_ok = True

    category_score = 1.0 if category_ok else 0.0
    score = round(0.5 * category_score + 0.5 * terms_score, 2)

    return {
        "key": "task_pass",
        "score": score,
        "comment": (
            f"category_ok={category_ok}, terms_ok={terms_ok}, "
            f"terms_score={terms_score:.2f}, score={score:.2f}"
        ),
    }
