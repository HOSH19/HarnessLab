"""Task pass/fail evaluator for ticket triage outputs.

Checks classification and reply content against task fixtures.
Does not call LLMs or access observability backends directly.
"""

from harnesslab.eval.outputs import run_output_field


def task_pass(run, example) -> dict:
    """Score whether the agent produced a correct triage result."""
    outputs = run.outputs or {}
    reference = example.outputs or example.inputs or {}
    expected_category = reference.get("expected_category", "")
    required_terms = reference.get("required_reply_terms", [])

    classification = str(run_output_field(outputs, "classification", "")).lower()
    reply = str(run_output_field(outputs, "final_reply", "")).lower()

    category_ok = expected_category.lower() in classification if expected_category else True
    if required_terms:
        matched_terms = [term for term in required_terms if term.lower() in reply]
        missing_terms = [term for term in required_terms if term.lower() not in reply]
        terms_score = len(matched_terms) / len(required_terms)
        terms_ok = not missing_terms
    else:
        missing_terms = []
        terms_score = 1.0
        terms_ok = True

    category_score = 1.0 if category_ok else 0.0
    score = round(0.5 * category_score + 0.5 * terms_score, 2)

    return {
        "key": "task_pass",
        "score": score,
        "comment": (
            f"category_ok={category_ok}, terms_ok={terms_ok}, "
            f"terms_score={terms_score:.2f}, missing_terms={missing_terms}, score={score:.2f}"
        ),
    }
