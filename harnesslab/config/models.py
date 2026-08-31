"""Pydantic models for harness YAML configuration.

Defines the schema for harness variant configs. Validation only;
file loading is owned by config.loader.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExecutionConfig(BaseModel):
    """Controls graph execution limits and error handling."""

    max_turns: int = Field(default=10, ge=1, le=100)
    stop_on_tool_error: bool = False


class ToolingConfig(BaseModel):
    """Controls tool invocation retry and timeout behavior."""

    retry_count: int = Field(default=0, ge=0, le=5)
    tool_timeout_s: float = Field(default=30.0, ge=1.0)
    error_format: str = Field(default="minimal", pattern="^(minimal|verbose)$")
    cache_reads: bool = False
    circuit_breaker_threshold: int | None = Field(default=None, ge=1, le=10)


class ContextConfig(BaseModel):
    """Controls message history trimming before each model call."""

    history_limit: int | None = Field(default=None, ge=2)


class ObservabilityConfig(BaseModel):
    """Controls LangSmith tracing metadata for a harness variant.

    ``harness_name`` is injected by the runner; avoid duplicating dataset
    fields (model, flaky_tools) in ``trace_metadata``.
    """

    langsmith_project: str | None = None
    trace_metadata: dict[str, Any] = Field(default_factory=dict)


class HarnessConfig(BaseModel):
    """Top-level harness configuration loaded from a YAML file."""

    name: str
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    tooling: ToolingConfig = Field(default_factory=ToolingConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
