#!/usr/bin/env python3
"""
Test script for trace loading functionality.
"""

import json
import os
import tempfile
from trace_collector import TraceCollector

def test_single_json_object():
    """Test loading a single JSON object."""
    trace_data = {
        "agent_id": "test-agent",
        "input": "test input",
        "output": "test output",
        "status": "success",
        "steps": []
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(trace_data, f)
        temp_file = f.name

    try:
        collector = TraceCollector()
        collector.load_json_file(temp_file)
        traces = collector.get_traces()

        assert len(traces) == 1, f"Expected 1 trace, got {len(traces)}"
        assert traces[0].agent_id == "test-agent"
        print("✓ Single JSON object test passed")
    finally:
        os.unlink(temp_file)

def test_json_array():
    """Test loading a JSON array of objects."""
    trace_data = [
        {
            "agent_id": "test-agent-1",
            "input": "test input 1",
            "output": "test output 1",
            "status": "success",
            "steps": []
        },
        {
            "agent_id": "test-agent-2",
            "input": "test input 2",
            "output": "test output 2",
            "status": "success",
            "steps": []
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(trace_data, f)
        temp_file = f.name

    try:
        collector = TraceCollector()
        collector.load_json_file(temp_file)
        traces = collector.get_traces()

        assert len(traces) == 2, f"Expected 2 traces, got {len(traces)}"
        assert traces[0].agent_id == "test-agent-1"
        assert traces[1].agent_id == "test-agent-2"
        print("✓ JSON array test passed")
    finally:
        os.unlink(temp_file)

def test_json_lines():
    """Test loading JSON objects separated by newlines."""
    trace_data = [
        '{"agent_id": "test-agent-1", "input": "test input 1", "output": "test output 1", "status": "success", "steps": []}',
        '{"agent_id": "test-agent-2", "input": "test input 2", "output": "test output 2", "status": "success", "steps": []}'
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('\n'.join(trace_data))
        temp_file = f.name

    try:
        collector = TraceCollector()
        collector.load_json_file(temp_file)
        traces = collector.get_traces()

        assert len(traces) == 2, f"Expected 2 traces, got {len(traces)}"
        assert traces[0].agent_id == "test-agent-1"
        assert traces[1].agent_id == "test-agent-2"
        print("✓ JSON lines test passed")
    finally:
        os.unlink(temp_file)

def test_empty_file():
    """Test loading an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name

    try:
        collector = TraceCollector()
        collector.load_json_file(temp_file)
        traces = collector.get_traces()

        assert len(traces) == 0, f"Expected 0 traces, got {len(traces)}"
        print("✓ Empty file test passed")
    finally:
        os.unlink(temp_file)

def test_invalid_json():
    """Test loading a file with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"agent_id": "test-agent", "input": "test input", invalid json')
        temp_file = f.name

    try:
        collector = TraceCollector()
        collector.load_json_file(temp_file)
        traces = collector.get_traces()

        assert len(traces) == 0, f"Expected 0 traces, got {len(traces)}"
        print("✓ Invalid JSON test passed")
    finally:
        os.unlink(temp_file)

if __name__ == "__main__":
    print("Running trace loading tests...")
    test_single_json_object()
    test_json_array()
    test_json_lines()
    test_empty_file()
    test_invalid_json()
    print("All tests passed!")