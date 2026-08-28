"""Surface draft reply text as a LangSmith experiment column."""

from langsmith.schemas import Example, Run


def final_reply(run: Run, example: Example) -> dict:
    """Expose the agent draft reply as freeform feedback for the results table."""
    del example
    reply = str((run.outputs or {}).get("final_reply", "") or "").strip()
    return {
        "key": "reply_text",
        "value": reply or "(empty)",
        "score": 1.0 if reply else 0.0,
        "comment": "draft_reply tool output" if reply else "agent did not call draft_reply",
    }
