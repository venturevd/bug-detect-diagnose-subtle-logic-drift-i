"""
Workflow Type Detector

This module detects the type of workflow based on trace content.
"""

import json
from typing import Dict, Any


class WorkflowDetector:
    """
    Detects workflow type from agent traces.
    """

    # Keyword patterns for workflow type detection
    WORKFLOW_PATTERNS = {
        'agent': {
            'keywords': ['agent', 'task', 'operation'],
            'actions': ['run', 'execute', 'perform', 'complete']
        },
        'research': {
            'keywords': ['search', 'web', 'api', 'fetch', 'url', 'data', 'research', 'query'],
            'actions': ['search', 'query', 'look', 'investigate', 'research']
        },
        'code': {
            'keywords': ['code', 'function', 'method', 'class', 'api', 'implementation', 'build'],
            'actions': ['write', 'implement', 'refactor', 'debug', 'test', 'run']
        },
        'analysis': {
            'keywords': ['analyze', 'analyze', 'compare', 'evaluate', 'assess', 'review'],
            'actions': ['analyze', 'compare', 'evaluate', 'assess', 'review', 'summarize']
        },
        'creative': {
            'keywords': ['write', 'create', 'generate', 'design', 'draft', 'compose'],
            'actions': ['write', 'create', 'generate', 'design', 'draft', 'compose']
        },
        'qa': {
            'keywords': ['test', 'check', 'verify', 'validate', 'bug', 'issue', 'fix'],
            'actions': ['test', 'check', 'verify', 'validate', 'find', 'debug']
        }
    }

    @classmethod
    def detect(cls, trace: Dict[str, Any]) -> str:
        """
        Detect workflow type from a trace.

        Args:
            trace (dict): Dictionary containing trace data

        Returns:
            str: Detected workflow type
        """
        scores = {}

        # Check steps for keywords
        if 'steps' in trace:
            for step in trace['steps']:
                # Check action keywords
                if 'action' in step:
                    cls._score_workflow_type(scores, step['action'])

                # Check reasoning/content
                if 'reasoning' in step:
                    cls._score_workflow_type(scores, step['reasoning'])

        # Check input/output for keywords
        if 'input' in trace:
            cls._score_workflow_type(scores, trace['input'])

        if 'output' in trace:
            cls._score_workflow_type(scores, trace['output'])

        # Check agent_id for clues
        if 'agent_id' in trace:
            cls._score_workflow_type(scores, trace['agent_id'])

        # Return the workflow type with the highest score
        if scores:
            return max(scores, key=scores.get)
        return 'general'

    @classmethod
    def _score_workflow_type(cls, scores: Dict[str, float], text: str) -> None:
        """
        Score workflow types based on keywords found in text.

        Args:
            scores (dict): Dictionary to update with scores
            text (str): Text to search for keywords
        """
        text_lower = text.lower()

        for workflow_type, patterns in cls.WORKFLOW_PATTERNS.items():
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    scores[workflow_type] = scores.get(workflow_type, 0) + 1

            # Check action phrases
            for action in patterns['actions']:
                if action in text_lower:
                    scores[workflow_type] = scores.get(workflow_type, 0) + 1

    @classmethod
    def classify_batch(cls, traces: list) -> Dict[str, int]:
        """
        Classify multiple traces and return workflow distribution.

        Args:
            traces (list): List of trace dictionaries

        Returns:
            dict: Workflow type distribution
        """
        distribution = {}

        for trace in traces:
            workflow_type = cls.detect(trace)
            distribution[workflow_type] = distribution.get(workflow_type, 0) + 1

        return distribution