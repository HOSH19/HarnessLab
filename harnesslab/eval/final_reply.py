"""Surface draft reply text as a LangSmith experiment column."""

from langsmith.schemas import Example, Run


def reply_text(run: Run, example: Example) -> dict:
    """Expose draft reply presence and text without colliding with Outputs display."""
    del example
    reply = str((run.outputs or {}).get("final_reply", "") or "").strip()
    return {
        "key": "reply_text",
        "score": 1.0 if reply else 0.0,
        "comment": reply if reply else "(empty — agent did not call draft_reply)",
    }
