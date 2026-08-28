"""Pipeline completion helpers for ticket-triage routing."""

from langchain_core.messages import AIMessage, HumanMessage

from harnesslab.graph.extract import extract_tool_names_from_messages
from harnesslab.graph.state import AgentState

NUDGE_MESSAGE = (
    "Required: call the classify tool, then draft_reply, before ending. "
    "Do not respond with plain text only."
)

REQUIRED_TOOLS = ("classify", "draft_reply")


def pipeline_complete(messages: list) -> bool:
    """Return True when classify and draft_reply both appear in tool history."""
    names = extract_tool_names_from_messages(messages)
    return all(tool in names for tool in REQUIRED_TOOLS)


def already_nudged(messages: list) -> bool:
    """Return True when the pipeline nudge was already injected."""
    for message in messages:
        content = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
        if content == NUDGE_MESSAGE:
            return True
    return False


def should_continue_with_nudge(state: AgentState) -> str:
    """Route to tools, nudge incomplete pipelines once, or end."""
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    if not pipeline_complete(messages) and not already_nudged(messages):
        return "nudge"
    return "end"


def nudge_incomplete_pipeline(state: AgentState) -> dict:
    """Inject a reminder when the agent tries to stop before classify/draft_reply."""
    return {"messages": [HumanMessage(content=NUDGE_MESSAGE)]}
