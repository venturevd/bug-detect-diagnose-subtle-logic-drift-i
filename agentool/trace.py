"""
ReasoningTrace — structured record of one agent execution.

Emitted by agents, consumed by debuggers, monitors, and evaluators.

Usage:
    trace = ReasoningTrace(agent_id="my-agent", input="What is X?")
    trace.add_reasoning("I need to search for X.")
    call = ToolCall(name="search_web", arguments={"query": "X"})
    trace.add_tool_call(call)
    trace.add_tool_result(ToolResult(call_id=call.id, output=[...]))
    trace.finish(output="X is Y.", status=TraceStatus.SUCCESS)
    print(trace.to_dict())
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .tool import ToolCall, ToolResult


class StepType(str, Enum):
    REASONING    = "reasoning"
    TOOL_CALL    = "tool_call"
    TOOL_RESULT  = "tool_result"
    HANDOFF      = "handoff"
    MEMORY_READ  = "memory_read"
    MEMORY_WRITE = "memory_write"


class TraceStatus(str, Enum):
    SUCCESS          = "success"
    ERROR            = "error"
    LOOP_DETECTED    = "loop_detected"
    CONTEXT_OVERFLOW = "context_overflow"
    TIMEOUT          = "timeout"
    REFUSAL          = "refusal"
    IN_PROGRESS      = "in_progress"


@dataclass
class TraceStep:
    """One step in a reasoning trace."""
    type: StepType
    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:6]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # reasoning step
    content: str | None = None
    context_tokens: int = 0

    # tool_call step
    tool_call: ToolCall | None = None

    # tool_result step
    tool_result: ToolResult | None = None

    # handoff step
    to_agent: str | None = None
    handoff_message: str | None = None

    # memory steps
    query: str | None = None
    results: list | None = None
    memory_key: str | None = None
    memory_content: str | None = None

    # catch-all extra
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "step_id": self.step_id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.content is not None:
            d["content"] = self.content
        if self.context_tokens:
            d["context_tokens"] = self.context_tokens
        if self.tool_call is not None:
            d["tool_call"] = self.tool_call.to_dict()
        if self.tool_result is not None:
            d["tool_result"] = self.tool_result.to_dict()
        if self.to_agent:
            d["to_agent"] = self.to_agent
            d["message"] = self.handoff_message
        if self.query:
            d["query"] = self.query
        if self.results is not None:
            d["results"] = self.results
        if self.memory_key:
            d["key"] = self.memory_key
        if self.memory_content:
            d["content"] = self.memory_content
        d.update(self.extra)
        return d


@dataclass
class TraceMetrics:
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0
    step_count: int = 0
    tool_call_count: int = 0

    def to_dict(self) -> dict:
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "total_duration_ms": self.total_duration_ms,
            "step_count": self.step_count,
            "tool_call_count": self.tool_call_count,
        }


@dataclass
class ReasoningTrace:
    """Full execution record for one agent invocation."""
    agent_id: str
    input: str
    trace_id: str = field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:6]}")
    session_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    output: str | None = None
    status: TraceStatus = TraceStatus.IN_PROGRESS
    steps: list[TraceStep] = field(default_factory=list)
    metrics: TraceMetrics = field(default_factory=TraceMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Builder helpers ───────────────────────────────────────────────────────

    def add_reasoning(self, content: str, context_tokens: int = 0) -> TraceStep:
        step = TraceStep(
            type=StepType.REASONING,
            content=content,
            context_tokens=context_tokens,
        )
        self.steps.append(step)
        self.metrics.step_count += 1
        return step

    def add_tool_call(self, call: ToolCall) -> TraceStep:
        step = TraceStep(type=StepType.TOOL_CALL, tool_call=call)
        self.steps.append(step)
        self.metrics.step_count += 1
        self.metrics.tool_call_count += 1
        return step

    def add_tool_result(self, result: ToolResult) -> TraceStep:
        step = TraceStep(type=StepType.TOOL_RESULT, tool_result=result)
        self.steps.append(step)
        self.metrics.step_count += 1
        if result.duration_ms:
            self.metrics.total_duration_ms += result.duration_ms
        return step

    def finish(
        self,
        output: str,
        status: TraceStatus = TraceStatus.SUCCESS,
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
    ) -> None:
        self.output = output
        self.status = status
        self.finished_at = datetime.now(timezone.utc)
        if total_tokens:
            self.metrics.total_tokens = total_tokens
        if total_cost_usd:
            self.metrics.total_cost_usd = total_cost_usd
        if self.finished_at and self.started_at:
            elapsed = (self.finished_at - self.started_at).total_seconds() * 1000
            self.metrics.total_duration_ms = int(elapsed)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "input": self.input,
            "output": self.output,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
        }

    # ── Analysis helpers ──────────────────────────────────────────────────────

    def tool_calls(self) -> list[ToolCall]:
        return [s.tool_call for s in self.steps if s.tool_call is not None]

    def reasoning_steps(self) -> list[str]:
        return [s.content for s in self.steps if s.type == StepType.REASONING and s.content]

    def has_loop(self, window: int = 3) -> bool:
        """Detect if the agent repeated the same tool call multiple times in a row."""
        calls = [s.tool_call.name for s in self.steps if s.tool_call]
        if len(calls) < window:
            return False
        for i in range(len(calls) - window + 1):
            if len(set(calls[i:i+window])) == 1:
                return True
        return False
