"""
ToolSpec, ToolCall, ToolResult — the common tool interface.

Usage:
    spec = ToolSpec(
        name="search_web",
        description="Search the web. Use when you need current information.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )
    print(spec.to_openai())      # OpenAI function calling format
    print(spec.to_anthropic())   # Anthropic tool use format
    print(spec.to_dict())        # Canonical spec format
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ToolSpec:
    """Describes a callable tool in framework-agnostic form."""
    name: str
    description: str
    parameters: dict[str, Any]                   # JSON Schema object
    returns: dict[str, Any] | None = None        # JSON Schema for return value
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.returns:
            d["returns"] = self.returns
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    def to_openai(self) -> dict:
        """OpenAI function calling / tool_choice format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def to_anthropic(self) -> dict:
        """Anthropic tool use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ToolSpec":
        return cls(
            name=d["name"],
            description=d["description"],
            parameters=d["parameters"],
            returns=d.get("returns"),
            metadata=d.get("metadata", {}),
        )

    @classmethod
    def from_openai(cls, d: dict) -> "ToolSpec":
        """Parse from OpenAI function calling format."""
        fn = d.get("function", d)
        return cls(
            name=fn["name"],
            description=fn.get("description", ""),
            parameters=fn.get("parameters", {"type": "object", "properties": {}}),
        )

    @classmethod
    def from_anthropic(cls, d: dict) -> "ToolSpec":
        """Parse from Anthropic tool use format."""
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            parameters=d.get("input_schema", {"type": "object", "properties": {}}),
        )

    @property
    def has_side_effects(self) -> bool:
        return bool(self.metadata.get("side_effects", False))

    @property
    def cost_tier(self) -> str:
        return self.metadata.get("cost_tier", "unknown")


@dataclass
class ToolCall:
    """A record of an agent invoking a tool."""
    name: str
    arguments: dict[str, Any]
    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolResult:
    """The result of a tool call."""
    call_id: str
    output: Any
    error: str | None = None
    duration_ms: int = 0
    cost_tokens: int = 0

    @property
    def success(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "cost_tokens": self.cost_tokens,
        }
