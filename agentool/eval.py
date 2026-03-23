"""
EvalCase, Assertion, EvalResult — property-based evaluation for non-deterministic agents.

Design: assertions are properties the output should have, not exact matches.
This handles the fundamental non-determinism of LLM-based agents.

Usage:
    case = EvalCase(
        case_id="search_001",
        description="Agent should use search and cite sources",
        input="What debugging tools exist for AI agents?",
        assertions=[
            Assertion(type="contains_tool_call", tool_name="search_web"),
            Assertion(type="output_property", property="mentions at least 2 tool names"),
        ],
    )
    # Run your agent, collect the trace, then evaluate:
    result = evaluate(case, trace, judge_fn=my_llm_judge)
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .trace import ReasoningTrace


@dataclass
class Assertion:
    """One property the agent output should satisfy."""
    type: str           # see AssertionType constants below
    description: str = ""

    # output_property
    property: str | None = None

    # contains_tool_call
    tool_name: str | None = None
    tool_args: dict | None = None  # if set, call must include these args

    # tool_call_count
    min_calls: int | None = None
    max_calls: int | None = None

    # response_format
    schema: dict | None = None

    # latency
    max_ms: int | None = None

    # context_efficiency
    max_tokens: int | None = None

    # catch-all
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"type": self.type}
        if self.description:
            d["description"] = self.description
        for attr in ("property", "tool_name", "tool_args", "min_calls", "max_calls",
                     "schema", "max_ms", "max_tokens"):
            v = getattr(self, attr)
            if v is not None:
                d[attr] = v
        d.update(self.extra)
        return d


# ── Assertion type constants ───────────────────────────────────────────────────

class AssertionType:
    OUTPUT_PROPERTY    = "output_property"    # LLM-judged property
    CONTAINS_TOOL_CALL = "contains_tool_call" # specific tool was called
    TOOL_CALL_COUNT    = "tool_call_count"    # number of tool calls
    NO_HALLUCINATION   = "no_hallucination"   # output grounded in context
    RESPONSE_FORMAT    = "response_format"    # output matches schema
    CONTEXT_EFFICIENCY = "context_efficiency" # token budget
    LATENCY            = "latency"            # timing constraint


@dataclass
class EvalCase:
    """A test case for an agent. Framework-agnostic."""
    case_id: str
    description: str
    input: str
    assertions: list[Assertion] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)  # extra context for the agent
    tags: list[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy | medium | hard
    eval_id: str = field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:6]}")

    def to_dict(self) -> dict:
        return {
            "eval_id": self.eval_id,
            "case_id": self.case_id,
            "description": self.description,
            "input": self.input,
            "assertions": [a.to_dict() for a in self.assertions],
            "context": self.context,
            "tags": self.tags,
            "difficulty": self.difficulty,
        }


@dataclass
class AssertionResult:
    """Result for one assertion."""
    assertion_type: str
    passed: bool
    score: float        # 0.0–1.0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "assertion_type": self.assertion_type,
            "passed": self.passed,
            "score": self.score,
            "reason": self.reason,
        }


@dataclass
class EvalResult:
    """Result of evaluating one EvalCase against one trace."""
    eval_id: str
    case_id: str
    trace_id: str
    passed: bool
    assertion_results: list[AssertionResult]
    composite_score: float
    judge_model: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "eval_id": self.eval_id,
            "case_id": self.case_id,
            "trace_id": self.trace_id,
            "passed": self.passed,
            "assertion_results": [r.to_dict() for r in self.assertion_results],
            "composite_score": self.composite_score,
            "judge_model": self.judge_model,
            "evaluated_at": self.evaluated_at.isoformat(),
            "notes": self.notes,
        }

    @property
    def failed_assertions(self) -> list[AssertionResult]:
        return [r for r in self.assertion_results if not r.passed]


# ── Built-in evaluators (no LLM needed) ───────────────────────────────────────

def evaluate_structural(case: EvalCase, trace: ReasoningTrace) -> list[AssertionResult]:
    """
    Evaluate assertions that don't require an LLM judge.
    Returns results for: contains_tool_call, tool_call_count, latency, context_efficiency.
    """
    results = []
    tool_names = [tc.name for tc in trace.tool_calls()]

    for assertion in case.assertions:
        if assertion.type == AssertionType.CONTAINS_TOOL_CALL:
            if assertion.tool_name is None:
                passed = len(tool_names) > 0
                reason = f"{len(tool_names)} tool calls made"
            else:
                passed = assertion.tool_name in tool_names
                reason = (
                    f"Found {assertion.tool_name}" if passed
                    else f"{assertion.tool_name} not in {tool_names}"
                )
            results.append(AssertionResult(
                assertion_type=assertion.type,
                passed=passed,
                score=1.0 if passed else 0.0,
                reason=reason,
            ))

        elif assertion.type == AssertionType.TOOL_CALL_COUNT:
            count = len(tool_names)
            passed = True
            if assertion.min_calls is not None and count < assertion.min_calls:
                passed = False
            if assertion.max_calls is not None and count > assertion.max_calls:
                passed = False
            results.append(AssertionResult(
                assertion_type=assertion.type,
                passed=passed,
                score=1.0 if passed else 0.0,
                reason=f"{count} tool calls (min={assertion.min_calls}, max={assertion.max_calls})",
            ))

        elif assertion.type == AssertionType.LATENCY:
            if assertion.max_ms is not None:
                passed = trace.metrics.total_duration_ms <= assertion.max_ms
                results.append(AssertionResult(
                    assertion_type=assertion.type,
                    passed=passed,
                    score=1.0 if passed else 0.0,
                    reason=f"{trace.metrics.total_duration_ms}ms (max={assertion.max_ms}ms)",
                ))

        elif assertion.type == AssertionType.CONTEXT_EFFICIENCY:
            if assertion.max_tokens is not None:
                passed = trace.metrics.total_tokens <= assertion.max_tokens
                results.append(AssertionResult(
                    assertion_type=assertion.type,
                    passed=passed,
                    score=1.0 if passed else 0.0,
                    reason=f"{trace.metrics.total_tokens} tokens (max={assertion.max_tokens})",
                ))

    return results


def evaluate(
    case: EvalCase,
    trace: ReasoningTrace,
    judge_fn: Callable[[str, str, str], tuple[bool, float, str]] | None = None,
    judge_model: str = "",
) -> EvalResult:
    """
    Evaluate a trace against an EvalCase.

    judge_fn(output, context, property_description) -> (passed, score, reason)
    Required for output_property and no_hallucination assertions.
    If not provided, only structural assertions are evaluated.
    """
    all_results = evaluate_structural(case, trace)

    # LLM-judged assertions
    if judge_fn is not None:
        context = str(trace.tool_calls()) + "\n\n" + "\n".join(trace.reasoning_steps())
        for assertion in case.assertions:
            if assertion.type in (AssertionType.OUTPUT_PROPERTY, AssertionType.NO_HALLUCINATION):
                prop = assertion.property or assertion.type
                passed, score, reason = judge_fn(trace.output or "", context, prop)
                all_results.append(AssertionResult(
                    assertion_type=assertion.type,
                    passed=passed,
                    score=score,
                    reason=reason,
                ))

    composite = (sum(r.score for r in all_results) / len(all_results)) if all_results else 0.0
    return EvalResult(
        eval_id=case.eval_id,
        case_id=case.case_id,
        trace_id=trace.trace_id,
        passed=all(r.passed for r in all_results),
        assertion_results=all_results,
        composite_score=round(composite, 3),
        judge_model=judge_model,
    )
