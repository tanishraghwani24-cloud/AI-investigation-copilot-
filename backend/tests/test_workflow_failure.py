from app.graph.workflow import _identify_failed_node, REPORTING, CONTEXT, REASONING
from app.schemas.investigation_state import AgentStatus

def test_identify_failed_node_reporting_missing():
    state = {
        "context_intelligence": {"status": AgentStatus.COMPLETED.value},
        "investigation_reasoning": {"status": AgentStatus.COMPLETED.value},
        "evidence_compliance_validation": {"status": AgentStatus.COMPLETED.value},
        "decision_optimization": {"status": AgentStatus.COMPLETED.value},
    }
    failed_node = _identify_failed_node(state)
    assert failed_node == REPORTING

def test_identify_failed_node_reporting_failed():
    state = {
        "context_intelligence": {"status": AgentStatus.COMPLETED.value},
        "investigation_reasoning": {"status": AgentStatus.COMPLETED.value},
        "evidence_compliance_validation": {"status": AgentStatus.COMPLETED.value},
        "decision_optimization": {"status": AgentStatus.COMPLETED.value},
        "investigation_report": {"status": AgentStatus.FAILED.value}
    }
    failed_node = _identify_failed_node(state)
    assert failed_node == REPORTING

def test_identify_failed_node_context_missing():
    state = {}
    failed_node = _identify_failed_node(state)
    assert failed_node == CONTEXT

def test_identify_failed_node_reasoning_in_progress():
    state = {
        "context_intelligence": {"status": AgentStatus.COMPLETED.value},
        "investigation_reasoning": {"status": AgentStatus.IN_PROGRESS.value},
    }
    failed_node = _identify_failed_node(state)
    assert failed_node == REASONING
