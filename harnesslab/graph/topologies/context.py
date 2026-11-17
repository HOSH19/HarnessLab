"""Shared context passed into topology compilers."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from harnesslab.config.graph_models import GraphConfig
from harnesslab.config.models import HarnessConfig
from harnesslab.graph.state import AgentState


@dataclass
class TopologyContext:
    """Inputs required to compile a named topology for an example agent."""

    harness: HarnessConfig
    graph: GraphConfig
    tools: list[Any]
    call_model: Callable[[AgentState], dict]
    role_prompts: dict[str, str] = field(default_factory=dict)
    tool_groups: dict[str, list[Any]] | None = None
