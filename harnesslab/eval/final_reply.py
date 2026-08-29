"""Surface draft reply text as a Langfuse experiment column."""

from harnesslab.eval.outputs import run_output_field


def reply_text(run, example) -> dict:
    """Expose draft reply presence and text without colliding with Outputs display."""
    del example
    reply = str(run_output_field(run.outputs or {}, "final_reply", "") or "").strip()
    return {
        "key": "reply_text",
        "score": 1.0 if reply else 0.0,
        "comment": reply if reply else "(empty — agent did not call draft_reply)",
    }
