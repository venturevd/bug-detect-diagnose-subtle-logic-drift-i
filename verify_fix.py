#!/usr/bin/env python3
"""
Verification script for the trace loading bug fix.
"""

import json
import os
import tempfile
import subprocess

def create_test_data():
    """Create test data files."""
    # Single JSON object
    with open('test_single.json', 'w') as f:
        json.dump({
            "agent_id": "test-agent-1",
            "input": "test input 1",
            "output": "test output 1",
            "status": "success",
            "steps": []
        }, f)

    # JSON array
    with open('test_array.json', 'w') as f:
        json.dump([
            {
                "agent_id": "test-agent-2",
                "input": "test input 2",
                "output": "test output 2",
                "status": "success",
                "steps": []
            },
            {
                "agent_id": "test-agent-3",
                "input": "test input 3",
                "output": "test output 3",
                "status": "success",
                "steps": []
            }
        ], f)

    # JSON lines
    with open('test_lines.json', 'w') as f:
        f.write('{"agent_id": "test-agent-4", "input": "test input 4", "output": "test output 4", "status": "success", "steps": []}\n')
        f.write('{"agent_id": "test-agent-5", "input": "test input 5", "output": "test output 5", "status": "success", "steps": []}\n')

def run_tests():
    """Run the test suite."""
    result = subprocess.run(['python3', 'test_trace_loading.py'],
                          capture_output=True, text=True)
    print("Test output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    return result.returncode == 0

def main():
    """Main verification function."""
    print("Creating test data...")
    create_test_data()

    print("\nRunning tests...")
    tests_passed = run_tests()

    if tests_passed:
        print("\n✓ All tests passed! The bug has been fixed.")
    else:
        print("\n✗ Some tests failed. The bug may not be fully fixed.")

    # Clean up
    for file in ['test_single.json', 'test_array.json', 'test_lines.json']:
        if os.path.exists(file):
            os.remove(file)

if __name__ == "__main__":
    main()