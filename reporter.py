"""
Reporter Module

This module generates reports and visualizations for drift analysis results.
"""

import matplotlib.pyplot as plt
import numpy as np

class Reporter:
    """
    Generates reports and visualizations for drift analysis.
    """

    def __init__(self):
        """
        Initialize the reporter.
        """
        pass

    def generate_text_report(self, analysis_results):
        """
        Generate a text report from drift analysis results.

        Args:
            analysis_results (dict): Results from drift analysis

        Returns:
            str: Text report
        """
        report_lines = ["Drift Analysis Report"]
        report_lines.append("=" * 50)

        for feature, result in analysis_results.items():
            report_lines.append(f"\n{feature.capitalize()} Drift Analysis:")
            report_lines.append(f"  - Has drift: {result['has_drift']}")
            report_lines.append(f"  - P-value: {result['p_value']:.4f}")
            report_lines.append(f"  - Statistic: {result['statistic']:.4f}")
            report_lines.append(f"  - Distance: {result['distance']:.4f}")

        return "\n".join(report_lines)

    def generate_histogram(self, baseline_data, current_data, feature_name, output_file):
        """
        Generate a histogram comparing baseline and current data.

        Args:
            baseline_data (list): Baseline data for the feature
            current_data (list): Current data for the feature
            feature_name (str): Name of the feature
            output_file (str): Path to save the histogram
        """
        plt.figure(figsize=(10, 6))
        plt.hist(baseline_data, bins=20, alpha=0.5, label='Baseline', color='blue')
        plt.hist(current_data, bins=20, alpha=0.5, label='Current', color='red')
        plt.title(f'{feature_name.capitalize()} Distribution Comparison')
        plt.xlabel(feature_name)
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_file)
        plt.close()

    def generate_time_series(self, data, feature_name, output_file):
        """
        Generate a time series plot for a feature.

        Args:
            data (list): Data for the feature
            feature_name (str): Name of the feature
            output_file (str): Path to save the time series plot
        """
        plt.figure(figsize=(10, 6))
        plt.plot(data, marker='o', linestyle='-', color='green')
        plt.title(f'{feature_name.capitalize()} Time Series')
        plt.xlabel('Execution')
        plt.ylabel(feature_name)
        plt.grid(True)
        plt.savefig(output_file)
        plt.close()