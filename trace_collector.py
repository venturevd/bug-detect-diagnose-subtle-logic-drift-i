"""
Trace Collector Module

This module collects and validates agent execution traces using the agent-tool-spec format.
"""

import json
import csv
from datetime import datetime
from agentool import ReasoningTrace, TraceStatus, TraceMetrics, ToolCall, ToolResult, StepType, TraceStep

class TraceCollector:
    """
    Collects and validates agent execution traces.
    """

    def __init__(self):
        """
        Initialize the trace collector.
        """
        self.traces = []

    def load_from_json(self, file_path):
        """
        Load traces from a JSON file.

        Args:
            file_path (str): Path to the JSON file
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                try:
                    trace = self._create_trace_from_dict(item)
                    self.traces.append(trace)
                except Exception as e:
                    print(f"Warning: Skipping invalid trace: {e}")
        elif isinstance(data, dict):
            try:
                trace = self._create_trace_from_dict(data)
                self.traces.append(trace)
            except Exception as e:
                print(f"Warning: Invalid trace in file: {e}")

    def load_from_json_line(self, json_line):
        """
        Load a single trace from a JSON line.

        Args:
            json_line (str): JSON string representing a trace
        """
        try:
            # Remove comments and extra whitespace
            json_line = json_line.strip()
            if json_line.startswith('#') or not json_line:
                return

            # Parse JSON
            data = json.loads(json_line)
            trace = self._create_trace_from_dict(data)
            self.traces.append(trace)
        except Exception as e:
            print(f"Warning: Skipping invalid trace: {e}")

    def load_json_file(self, file_path):
        """
        Load traces from a JSON file, handling both single objects and arrays.

        Args:
            file_path (str): Path to the JSON file
        """
        with open(file_path, 'r') as f:
            content = f.read()

            # Check if content contains multiple JSON objects separated by newlines
            if '\n' in content:
                for line in content.split('\n'):
                    if line.strip():
                        self.load_from_json_line(line)
            else:
                # Try to load as a single JSON object or array
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            try:
                                trace = self._create_trace_from_dict(item)
                                self.traces.append(trace)
                            except Exception as e:
                                print(f"Warning: Skipping invalid trace: {e}")
                    elif isinstance(data, dict):
                        try:
                            trace = self._create_trace_from_dict(data)
                            self.traces.append(trace)
                        except Exception as e:
                            print(f"Warning: Invalid trace in file: {e}")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")

    def load_from_csv(self, file_path):
        """
        Load traces from a CSV file.

        Args:
            file_path (str): Path to the CSV file
        """
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    trace = self._create_trace_from_dict(row)
                    self.traces.append(trace)
                except Exception as e:
                    print(f"Warning: Skipping invalid trace: {e}")

    def _create_trace_from_dict(self, data):
        """
        Create a ReasoningTrace from a dictionary.

        Args:
            data (dict): Dictionary containing trace data

        Returns:
            ReasoningTrace: Created trace object
        """
        # Create a basic trace with required fields
        trace = ReasoningTrace(
            agent_id=data.get('agent_id', 'unknown'),
            input=data.get('input', 'unknown')
        )

        # Set optional fields
        if 'output' in data:
            trace.output = data['output']
        if 'status' in data:
            trace.status = TraceStatus(data['status'])
        if 'session_id' in data:
            trace.session_id = data['session_id']
        if 'trace_id' in data:
            trace.trace_id = data['trace_id']
        if 'started_at' in data:
            trace.started_at = datetime.fromisoformat(data['started_at'])
        if 'finished_at' in data and data['finished_at']:
            trace.finished_at = datetime.fromisoformat(data['finished_at'])
        if 'metrics' in data:
            metrics = data['metrics']
            trace.metrics = TraceMetrics(
                total_tokens=metrics.get('total_tokens', 0),
                total_cost_usd=metrics.get('total_cost_usd', 0.0),
                total_duration_ms=metrics.get('total_duration_ms', 0),
                step_count=metrics.get('step_count', 0),
                tool_call_count=metrics.get('tool_call_count', 0)
            )
        if 'metadata' in data:
            trace.metadata = data['metadata']

        # Add steps
        if 'steps' in data:
            for step_data in data['steps']:
                step_type = StepType(step_data.get('type', 'reasoning'))
                step = TraceStep(type=step_type)

                if step_type == StepType.REASONING:
                    step.content = step_data.get('content', '')
                    step.context_tokens = step_data.get('context_tokens', 0)
                elif step_type == StepType.TOOL_CALL:
                    tool_call_data = step_data.get('tool_call', {})
                    step.tool_call = ToolCall(
                        name=tool_call_data.get('name', 'unknown'),
                        arguments=tool_call_data.get('arguments', {})
                    )
                elif step_type == StepType.TOOL_RESULT:
                    tool_result_data = step_data.get('tool_result', {})
                    step.tool_result = ToolResult(
                        call_id=tool_result_data.get('call_id', 'unknown'),
                        output=tool_result_data.get('output', []),
                        duration_ms=tool_result_data.get('duration_ms', 0)
                    )

                trace.steps.append(step)

        return trace

    def validate_traces(self):
        """
        Validate all collected traces.

        Returns:
            list: List of validation errors
        """
        errors = []
        for trace in self.traces:
            try:
                # Basic validation
                if not trace.agent_id:
                    errors.append(f"Trace {trace.trace_id}: Missing agent_id")
                if not trace.input:
                    errors.append(f"Trace {trace.trace_id}: Missing input")
                if trace.status == TraceStatus.IN_PROGRESS and not trace.output:
                    errors.append(f"Trace {trace.trace_id}: In-progress trace without output")
            except Exception as e:
                errors.append(f"Trace {trace.trace_id}: {str(e)}")
        return errors

    def get_traces(self):
        """
        Get all collected traces.

        Returns:
            list: List of ReasoningTrace objects
        """
        return self.traces