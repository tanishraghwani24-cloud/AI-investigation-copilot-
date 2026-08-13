"""Passthrough (no-op) node functions for the investigation graph.

Each node accepts the current state and returns an empty update dict,
leaving the ``InvestigationState`` completely unchanged.  These nodes
exist solely to validate the pipeline wiring — real agent logic will
replace them in future rounds.
"""

from typing import Any


def context_passthrough(state: Any) -> dict:
    """No-op Context & Evidence Intelligence node."""
    return {}


def reasoning_passthrough(state: Any) -> dict:
    """No-op Investigation Reasoning node."""
    return {}


def compliance_passthrough(state: Any) -> dict:
    """No-op Evidence & Compliance Validation node."""
    return {}


def decision_passthrough(state: Any) -> dict:
    """No-op Decision Optimization node."""
    return {}


def reporting_passthrough(state: Any) -> dict:
    """No-op Reporting & Visualization node."""
    return {}
