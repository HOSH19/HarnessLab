"""Circuit breaker for repeated tool failures within a single run."""


class CircuitOpenError(RuntimeError):
    """Raised when a tool's circuit is open after consecutive failures."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Circuit open for tool: {tool_name}")


def record_tool_success(tool_name: str, context: dict) -> None:
    """Reset consecutive failure count after a successful tool call."""
    context["circuit_failures"].pop(tool_name, None)
    context["circuit_open"].discard(tool_name)


def record_tool_failure(tool_name: str, context: dict, *, threshold: int) -> None:
    """Increment failures and open the circuit when the threshold is reached."""
    failures = context["circuit_failures"].get(tool_name, 0) + 1
    context["circuit_failures"][tool_name] = failures
    if failures >= threshold:
        context["circuit_open"].add(tool_name)


def is_circuit_open(tool_name: str, context: dict) -> bool:
    """Return True when the tool circuit is open for this run."""
    return tool_name in context["circuit_open"]
