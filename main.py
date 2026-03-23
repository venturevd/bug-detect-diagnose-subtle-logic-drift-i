#!/usr/bin/env python3
"""
Detect and diagnose subtle logic drift in agent workflows.

This tool collects agent execution traces, analyzes them for logic drift using
statistical methods, and generates reports with the analysis results.

Bug fixed: The drift analysis reports now correctly show the number of traces loaded
and generate reports based on actual data rather than default values.
"""

import json
import os
import argparse
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
                try:
                    # Try to parse as JSON array first
                    traces.extend(json.load(f))
                    print(f"Loaded {len(traces)} traces from {json_file}")
                except json.JSONDecodeError:
                    # If that fails, try newline-separated objects
                    content = f.read()
                    objects = [json.loads(line) for line in content.strip().split('\n') if line.strip()]
                    traces.extend(objects)
                    print(f"Loaded {len(objects)} traces from {json_file} (newline format)")
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

    args = parser.parse_args()

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