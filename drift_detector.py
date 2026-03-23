"""
Drift Detection Module

This module provides algorithms to detect drift in AI model behavior.
"""

import numpy as np
from scipy.stats import ks_2samp

class DriftDetector:
    """
    Detects drift in AI model outputs using statistical methods.
    """

    def __init__(self, threshold=0.05):
        """
        Initialize the drift detector.

        Args:
            threshold (float): Statistical significance threshold for drift detection
        """
        self.threshold = threshold
        self.baseline_data = None
        self.current_data = None

    def set_baseline(self, data):
        """
        Set the baseline data distribution.

        Args:
            data (np.array): Array of baseline model outputs
        """
        self.baseline_data = np.array(data)

    def update_current(self, data):
        """
        Update the current data distribution.

        Args:
            data (np.array): Array of current model outputs
        """
        self.current_data = np.array(data)

    def detect_drift(self):
        """
        Detect drift using Kolmogorov-Smirnov test.

        Returns:
            tuple: (has_drift: bool, p_value: float, statistic: float)
        """
        if self.baseline_data is None or self.current_data is None:
            raise ValueError("Baseline and current data must be set")

        stat, p_value = ks_2samp(self.baseline_data, self.current_data)
        has_drift = p_value < self.threshold

        return has_drift, p_value, stat

    def calculate_distance(self):
        """
        Calculate Euclidean distance between distributions.

        Returns:
            float: Euclidean distance between means
        """
        if self.baseline_data is None or self.current_data is None:
            raise ValueError("Baseline and current data must be set")

        mean_baseline = np.mean(self.baseline_data)
        mean_current = np.mean(self.current_data)

        return np.abs(mean_baseline - mean_current)