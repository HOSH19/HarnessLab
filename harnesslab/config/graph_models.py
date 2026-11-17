"""Pydantic schema for graph topology variants."""

from typing import Literal

from pydantic import BaseModel, Field

TopologyName = Literal["react", "pipeline", "supervisor", "plan_execute"]


class GraphConfig(BaseModel):
    """Declarative selector for a compiled agent topology."""

    name: str
    topology: TopologyName = "react"
    roles: dict[str, str] = Field(default_factory=dict)
    max_workers: int | None = None
    require_verifier: bool = False
    expected_nodes: list[str] = Field(default_factory=list)
