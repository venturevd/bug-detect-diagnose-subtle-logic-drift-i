"""
agentool — reference implementation of the Agent Tool Interop Spec v0.1

Provides Python dataclasses for ToolSpec, ReasoningTrace, EvalCase, and EvalResult.
All types are JSON-serializable. Import what you need:

    from agentool import ToolSpec, ReasoningTrace, EvalCase, EvalResult
    from agentool.trace import TraceStep, StepType
"""
from .tool import ToolSpec, ToolCall, ToolResult
from .trace import ReasoningTrace, TraceStep, StepType, TraceStatus, TraceMetrics
from .eval import EvalCase, EvalResult, Assertion, AssertionResult

__version__ = "0.1.0"
__all__ = [
    "ToolSpec", "ToolCall", "ToolResult",
    "ReasoningTrace", "TraceStep", "StepType", "TraceStatus", "TraceMetrics",
    "EvalCase", "EvalResult", "Assertion", "AssertionResult",
]
