#!/usr/bin/env python3
"""
Detect and diagnose subtle logic drift in agent workflows.

This tool collects agent execution traces, analyzes them for logic drift using
statistical methods, and generates reports with the analysis results.

Bug fixed: The drift analysis reports now correctly show the number of traces loaded
and generate reports based on actual data rather than default values.

Step 3: Added --test command to verify analyze command behavior:
- Valid traces are processed correctly
- Invalid traces are skipped with appropriate warnings
- The count of loaded traces matches the number of valid traces
- Error cases are handled gracefully
"""

import json
import os
import argparse
import tempfile
import shutil
from collections import defaultdict
from scipy.stats import ks_2samp

def load_traces(directory):
    """
    Load agent execution traces from JSON files in the specified directory.

    Args:
        directory (str): Directory containing JSON trace files

    Returns:
        list: List of trace objects loaded from files
    """
    traces = []

    if not os.path.isdir(directory):
        print(f"Directory {directory} does not exist")
        return traces

    # Find all .json files in the directory
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]

    if not json_files:
        print(f"No JSON files found in {directory}")
        return traces

    # Load traces from each file
    for json_file in json_files:
        file_path = os.path.join(directory, json_file)
        try:
            with open(file_path, 'r') as f:
                content = f.read()

                # Try to parse as JSON array first
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        traces.extend(data)
                        print(f"Loaded {len(data)} traces from {json_file} (array format)")
                    else:
                        print(f"Warning: {json_file} is not a JSON array, skipping")
                except json.JSONDecodeError:
                    # If that fails, try newline-separated objects
                    # Handle both valid objects and empty lines
                    lines = content.strip().split('\n')
                    objects = []
                    for i, line in enumerate(lines):
                        if line.strip():
                            try:
                                objects.append(json.loads(line))
                            except json.JSONDecodeError:
                                print(f"Warning: Invalid JSON at line {i+1} in {json_file}, skipping")
                                continue
                    if objects:
                        traces.extend(objects)
                        print(f"Loaded {len(objects)} traces from {json_file} (newline format)")
                    else:
                        print(f"Warning: {json_file} is empty or not valid JSON, skipping")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    print(f"Total traces loaded: {len(traces)}")
    return traces

def analyze_drift(traces):
    """
    Analyze traces for logic drift using statistical methods.

    Args:
        traces (list): List of trace objects

    Returns:
        dict: Analysis results including drift detection
    """
    if not traces:
        return {
            'num_traces': 0,
            'drift_detected': False,
            'drift_score': 0.0,
            'analysis': 'No traces available for analysis'
        }

    # Group traces by workflow type
    workflow_groups = defaultdict(list)
    for trace in traces:
        workflow_type = trace.get('workflow_type', 'unknown')
        workflow_groups[workflow_type].append(trace)

    results = {
        'num_traces': len(traces),
        'workflow_distribution': {k: len(v) for k, v in workflow_groups.items()},
        'drift_results': {}
    }

    # For each workflow type, detect drift between batches
    for workflow_type, workflow_traces in workflow_groups.items():
        if len(workflow_traces) < 2:
            results['drift_results'][workflow_type] = {
                'drift_detected': False,
                'analysis': 'Insufficient traces for drift analysis'
            }
            continue

        # Split into two batches for comparison
        batch_size = len(workflow_traces) // 2
        batch1 = workflow_traces[:batch_size]
        batch2 = workflow_traces[batch_size:]

        # Extract features for comparison (e.g., execution time, step counts)
        feature1 = [len(trace.get('steps', [])) for trace in batch1]
        feature2 = [len(trace.get('steps', [])) for trace in batch2]

        if not feature1 or not feature2:
            results['drift_results'][workflow_type] = {
                'drift_detected': False,
                'analysis': 'No comparable features found'
            }
            continue

        # Perform Kolmogorov-Smirnov test for distribution difference
        try:
            stat, p_value = ks_2samp(feature1, feature2)
            drift_detected = p_value < 0.05  # 95% confidence threshold

            results['drift_results'][workflow_type] = {
                'drift_detected': drift_detected,
                'drift_score': float(stat),
                'p_value': float(p_value),
                'analysis': (
                    f"KS test statistic: {stat:.3f}, p-value: {p_value:.3f}"
                    f"{' - DRIFT DETECTED' if drift_detected else ''}"
                )
            }
        except Exception as e:
            results['drift_results'][workflow_type] = {
                'drift_detected': False,
                'analysis': f"Error in drift analysis: {str(e)}"
            }

    # Overall drift detection
    results['drift_detected'] = any(
        result.get('drift_detected') for result in results['drift_results'].values()
    )

    return results

def generate_report(analysis_results):
    """
    Generate a text report from analysis results.

    Args:
        analysis_results (dict): Results from analyze_drift function

    Returns:
        str: Formatted report text
    """
    report_lines = []

    # Header
    report_lines.append("=" * 60)
    report_lines.append("AGENT LOGIC DRIFT ANALYSIS REPORT")
    report_lines.append("=" * 60)

    # Summary
    report_lines.append(f"Total traces analyzed: {analysis_results['num_traces']}")
    report_lines.append(f"Workflows analyzed: {len(analysis_results['workflow_distribution'])}")
    report_lines.append(f"Overall drift detected: {'YES' if analysis_results['drift_detected'] else 'NO'}")
    report_lines.append("")

    # Workflow distribution
    report_lines.append("WORKFLOW DISTRIBUTION:")
    for workflow, count in analysis_results['workflow_distribution'].items():
        report_lines.append(f"  {workflow}: {count} traces")
    report_lines.append("")

    # Detailed results
    report_lines.append("DRIFT ANALYSIS RESULTS:")
    for workflow, result in analysis_results['drift_results'].items():
        report_lines.append(f"\nWorkflow: {workflow}")
        report_lines.append(f"  Drift detected: {'YES' if result['drift_detected'] else 'NO'}")
        if 'drift_score' in result:
            report_lines.append(f"  Drift score: {result['drift_score']:.3f}")
        if 'p_value' in result:
            report_lines.append(f"  P-value: {result['p_value']:.3f}")
        report_lines.append(f"  Analysis: {result['analysis']}")

    # Footer
    report_lines.append("=" * 60)
    report_lines.append("Report generated by Agent Logic Drift Analyzer")
    report_lines.append("=" * 60)

    return "\n".join(report_lines)

def run_test(dry_run=True):
    """
    Run test cases for the analyze command to verify:
    1. Valid traces are processed correctly
    2. Invalid traces are skipped with appropriate warnings
    3. The count of loaded traces matches the number of valid traces
    4. Error cases are handled gracefully

    Args:
        dry_run (bool): Whether to clean up test directory after test (default: True)

    Returns:
        tuple: (test_passed, test_details)
    """
    print("=" * 60)
    print("RUNNING TESTS FOR ANALYZE COMMAND")
    print("=" * 60)
    print()

    # Track test results
    test_passed = True
    test_details = []

    # Test 1: Valid traces newline-separated format
    print("Test 1: Valid traces in newline-separated format")
    test1_dir = tempfile.mkdtemp()
    try:
        with open(os.path.join(test1_dir, "valid_newline.json"), 'w') as f:
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')

        traces = load_traces(test1_dir)
        if len(traces) == 3:
            print("  ✓ PASS: Loaded 3 valid traces from newline format")
            test_details.append(("Valid newline format", True, "Loaded 3 traces"))
        else:
            print(f"  ✗ FAIL: Expected 3 traces, got {len(traces)}")
            test_passed = False
            test_details.append(("Valid newline format", False, f"Expected 3, got {len(traces)}"))
    finally:
        if dry_run:
            shutil.rmtree(test1_dir)
    print()

    # Test 2: Mixed valid and invalid traces
    print("Test 2: Mixed valid and invalid traces")
    test2_dir = tempfile.mkdtemp()
    try:
        with open(os.path.join(test2_dir, "mixed.json"), 'w') as f:
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')
            f.write('\n')  # Empty line (should be skipped)
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')
            f.write('{"invalid": json\n')  # Invalid JSON (should be skipped with warning)
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')

        traces = load_traces(test2_dir)
        if len(traces) == 3:
            print("  ✓ PASS: Loaded 3 valid traces, skipped 1 invalid")
            test_details.append(("Mixed valid/invalid traces", True, "Loaded 3, skipped 1 invalid"))
        else:
            print(f"  ✗ FAIL: Expected 3 valid traces, got {len(traces)}")
            test_passed = False
            test_details.append(("Mixed valid/invalid traces", False, f"Expected 3, got {len(traces)}"))
    finally:
        if dry_run:
            shutil.rmtree(test2_dir)
    print()

    # Test 3: Invalid directory handling
    print("Test 3: Invalid directory handling")
    traces = load_traces("/nonexistent/directory/xyz123")
    if len(traces) == 0:
        print("  ✓ PASS: Empty list returned for non-existent directory")
        test_details.append(("Invalid directory handling", True, "Empty list returned"))
    else:
        print(f"  ✗ FAIL: Expected empty list, got {len(traces)}")
        test_passed = False
        test_details.append(("Invalid directory handling", False, f"Expected empty, got {len(traces)}"))
    print()

    # Test 4: Empty directory handling
    print("Test 4: Empty directory handling")
    test4_dir = tempfile.mkdtemp()
    try:
        # Directory already created by mkdtemp, no need to mkdir
        traces = load_traces(test4_dir)
        if len(traces) == 0:
            print("  ✓ PASS: Empty list returned for empty directory")
            test_details.append(("Empty directory handling", True, "Empty list returned"))
        else:
            print(f"  ✗ FAIL: Expected empty list, got {len(traces)}")
            test_passed = False
            test_details.append(("Empty directory handling", False, f"Expected empty, got {len(traces)}"))
    finally:
        if dry_run:
            shutil.rmtree(test4_dir)
    print()

    # Test 5: Invalid JSON objects handling
    print("Test 5: Invalid JSON objects handling")
    test5_dir = tempfile.mkdtemp(prefix="drift_test5_")
    try:
        with open(os.path.join(test5_dir, "invalid_objects.json"), 'w') as f:
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')
            f.write('{"this is": not json\n')
            f.write('{"missing": "quote}\n')
            f.write('{"workflow_type": "agent", "steps": [{"action": "start"}]}\n')

        traces = load_traces(test5_dir)
        if len(traces) == 2:
            print("  ✓ PASS: Skipped 2 invalid JSON objects, loaded 2 valid traces")
            test_details.append(("Invalid JSON objects handling", True, "Skipped 2 invalid, loaded 2 valid"))
        else:
            print(f"  ✗ FAIL: Expected 2 valid traces, got {len(traces)}")
            test_passed = False
            test_details.append(("Invalid JSON objects handling", False, f"Expected 2, got {len(traces)}"))
    finally:
        if dry_run:
            shutil.rmtree(test5_dir)
    print()

    # Test 6: Directory with non-JSON files
    print("Test 6: Directory with non-JSON files")
    test6_dir = tempfile.mkdtemp()
    try:
        # Add some text files
        with open(os.path.join(test6_dir, "readme.txt"), 'w') as f:
            f.write("This is a README file\n")
        with open(os.path.join(test6_dir, "script.py"), 'w') as f:
            f.write("# A Python script\n")

        traces = load_traces(test6_dir)
        if len(traces) == 0:
            print("  ✓ PASS: Empty list returned when no JSON files present")
            test_details.append(("No JSON files handling", True, "Empty list returned"))
        else:
            print(f"  ✗ FAIL: Expected empty list, got {len(traces)}")
            test_passed = False
            test_details.append(("No JSON files handling", False, f"Expected empty, got {len(traces)}"))
    finally:
        if dry_run:
            shutil.rmtree(test6_dir)
    print()

    # Test 7: analyze_drift handles empty traces
    print("Test 7: analyze_drift with empty traces list")
    analysis = analyze_drift([])
    expected_keys = {'num_traces', 'drift_detected', 'drift_score', 'analysis'}
    if set(analysis.keys()) == expected_keys and analysis['num_traces'] == 0:
        print("  ✓ PASS: Empty traces handled correctly")
        test_details.append(("Empty traces handling", True, "Correct structure returned"))
    else:
        print(f"  ✗ FAIL: Expected correct structure, got {analysis}")
        test_passed = False
        test_details.append(("Empty traces handling", False, "Incorrect structure"))
    print()

    # Test 8: analyze_drift with single trace
    print("Test 8: analyze_drift with single trace (insufficient for drift analysis)")
    traces_single = [{"workflow_type": "agent", "steps": [{"action": "start"}]}]
    analysis = analyze_drift(traces_single)
    if (analysis['num_traces'] == 1 and
        'workflow_distribution' in analysis and
        analysis['drift_results']['agent']['drift_detected'] is False and
        'insufficient' in analysis['drift_results']['agent']['analysis'].lower()):
        print("  ✓ PASS: Single trace handled correctly (drift detection skipped)")
        test_details.append(("Single trace handling", True, "Drift analysis skipped gracefully"))
    else:
        print(f"  ✗ FAIL: Unexpected behavior with single trace: {analysis}")
        test_passed = False
        test_details.append(("Single trace handling", False, "Unexpected behavior"))
    print()

    # Test 9: analyze_drift detects drift between batches
    print("Test 9: analyze_drift detects drift between batches")
    test9_dir = tempfile.mkdtemp()
    try:
        # Batch 1: traces with 2 steps
        with open(os.path.join(test9_dir, "batch1.json"), 'w') as f:
            for i in range(10):
                f.write('{"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "end"}]}\n')
        # Batch 2: traces with 5 steps
        with open(os.path.join(test9_dir, "batch2.json"), 'w') as f:
            for i in range(10):
                f.write('{"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "step"}, {"action": "step"}, {"action": "step"}, {"action": "end"}]}\n')

        traces = load_traces(test9_dir)
        analysis = analyze_drift(traces)
        if analysis['num_traces'] == 20 and analysis['drift_detected'] is True:
            print("  ✓ PASS: Drift correctly detected between batches")
            test_details.append(("Drift detection", True, "Drift detected between batches"))
        else:
            print(f"  ✗ FAIL: Expected drift detection, got: {analysis}")
            test_passed = False
            test_details.append(("Drift detection", False, "Drift not detected"))
    finally:
        if dry_run:
            shutil.rmtree(test9_dir)
    print()

    # Test 10: analyze_drift with same batch size traces (should not detect drift)
    print("Test 10: analyze_drift with traces from same batch (no drift expected)")
    traces_same = [
        {"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "end"}]},
        {"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "end"}]},
        {"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "end"}]},
        {"workflow_type": "agent", "steps": [{"action": "start"}, {"action": "end"}]},
    ]
    analysis = analyze_drift(traces_same)
    if analysis['num_traces'] == 4 and not analysis['drift_detected']:
        print("  ✓ PASS: Same batch traces correctly analyzed")
        test_details.append(("Same batch analysis", True, "No drift detected as expected"))
    else:
        print(f"  ✗ FAIL: Expected no drift detection: {analysis}")
        test_passed = False
        test_details.append(("Same batch analysis", False, "Drift incorrectly detected"))
    print()

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result, _ in test_details if result)
    total = len(test_details)
    print(f"Tests passed: {passed}/{total}")
    print()

    for test_name, result, detail in test_details:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name} - {detail}")

    print()
    if test_passed:
        print("🎉 All tests PASSED!")
    else:
        print("⚠️  Some tests FAILED!")

    return test_passed, test_details

def main():
    """
    Main function to parse arguments and perform drift analysis.
    """
    parser = argparse.ArgumentParser(
        description='Detect and diagnose subtle logic drift in agent workflows'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing JSON trace files (default: current directory)'
    )
    parser.add_argument(
        '--output',
        help='Output file for the analysis report (default: print to console)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test cases for the analyze command'
    )

    args = parser.parse_args()

    # Run tests if --test flag is specified
    if args.test:
        run_test(dry_run=True)
        return

    # Load traces from the specified directory
    traces = load_traces(args.directory)

    if not traces:
        print("No traces available for analysis. Exiting.")
        return

    # Analyze traces for logic drift
    analysis_results = analyze_drift(traces)

    # Generate report
    report = generate_report(analysis_results)

    # Output report
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report generated: {args.output}")
        except Exception as e:
            print(f"Error writing report to {args.output}: {e}")
    else:
        print(report)

if __name__ == "__main__":
    main()