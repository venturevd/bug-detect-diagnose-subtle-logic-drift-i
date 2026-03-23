"""
Drift Analyzer Module

This module analyzes agent execution traces for logic drift using statistical methods.
"""

import numpy as np
from scipy.stats import ks_2samp
from drift_detector import DriftDetector

class DriftAnalyzer:
    """
    Analyzes agent execution traces for logic drift.
    """

    def __init__(self, threshold=0.05):
        """
        Initialize the drift analyzer.

        Args:
            threshold (float): Statistical significance threshold for drift detection
        """
        self.threshold = threshold
        self.detector = DriftDetector(threshold=threshold)

    def extract_features(self, traces):
        """
        Extract features from agent traces for drift analysis.

        Args:
            traces (list): List of ReasoningTrace objects

        Returns:
            dict: Dictionary of features extracted from traces
        """
        features = {
            'tool_call_counts': [],
            'reasoning_steps': [],
            'execution_times': [],
            'output_lengths': []
        }

        for trace in traces:
            features['tool_call_counts'].append(len(trace.tool_calls()))
            features['reasoning_steps'].append(len(trace.reasoning_steps()))
            features['execution_times'].append(trace.metrics.total_duration_ms)
            features['output_lengths'].append(len(trace.output) if trace.output else 0)

        return features

    def analyze_drift(self, baseline_traces, current_traces):
        """
        Analyze drift between baseline and current traces.

        Args:
            baseline_traces (list): List of baseline ReasoningTrace objects
            current_traces (list): List of current ReasoningTrace objects

        Returns:
            dict: Dictionary containing drift analysis results
        """
        baseline_features = self.extract_features(baseline_traces)
        current_features = self.extract_features(current_traces)

        results = {
            'tool_call_drift': self._analyze_feature_drift(
                baseline_features['tool_call_counts'],
                current_features['tool_call_counts']
            ),
            'reasoning_drift': self._analyze_feature_drift(
                baseline_features['reasoning_steps'],
                current_features['reasoning_steps']
            ),
            'execution_time_drift': self._analyze_feature_drift(
                baseline_features['execution_times'],
                current_features['execution_times']
            ),
            'output_length_drift': self._analyze_feature_drift(
                baseline_features['output_lengths'],
                current_features['output_lengths']
            )
        }

        return results

    def _analyze_feature_drift(self, baseline_data, current_data):
        """
        Analyze drift for a specific feature using statistical methods.

        Args:
            baseline_data (list): Baseline data for the feature
            current_data (list): Current data for the feature

        Returns:
            dict: Dictionary containing drift analysis results for the feature
        """
        if not baseline_data or not current_data:
            return {
                'has_drift': False,
                'p_value': 1.0,
                'statistic': 0.0,
                'distance': 0.0
            }

        self.detector.set_baseline(baseline_data)
        self.detector.update_current(current_data)

        has_drift, p_value, stat = self.detector.detect_drift()
        distance = self.detector.calculate_distance()

        return {
            'has_drift': has_drift,
            'p_value': p_value,
            'statistic': stat,
            'distance': distance
        }