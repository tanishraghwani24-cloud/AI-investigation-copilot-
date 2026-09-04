"""Regression tests for the report's entity-relationship graph.

The graph previously drew only the optional customer/merchant/beneficiary/device
records, so a real case carrying five transactions across six accounts rendered
as one isolated node with no edges. These tests pin the fix: every entity the
case actually supplies is graphed, and nothing that it does not supply is.
"""

from datetime import datetime

import pytest

from app.agents.reporting_agent import _build_entity_graph
from app.schemas.investigation_state import (
    BeneficiaryInfo,
    CaseInput,
    CustomerProfile,
    DeviceInfo,
    MerchantInfo,
    Transaction,
    create_initial_state,
)


def _txn(txn_id: str, sender: str, receiver: str, amount: float) -> Transaction:
    return Transaction(
        transaction_id=txn_id, amount=amount, currency="USD",
        timestamp=datetime(2025, 7, 15, 9, 0), sender_account=sender,
        receiver_account=receiver, transaction_type="WIRE", channel="ONLINE",
    )


def _state(case_input: CaseInput):
    return create_initial_state(case_id="CASE-ENTITY-GRAPH", case_input=case_input)


def _accounts_only_case() -> CaseInput:
    """The shape the Mock Bank account path produces: customer + transactions."""
    return CaseInput(
        alert_reason="Rapid outbound transfers",
        customer_profile=CustomerProfile(customer_id="CUST-001", name="Test Customer"),
        transactions=[
            _txn("TXN-001", "ACC-SRC", "ACC-DST-1", 48000.0),
            _txn("TXN-002", "ACC-SRC", "ACC-DST-2", 52500.0),
        ],
    )


class TestAccountsAndTransfers:
    """Accounts are required fields on every transaction, so always graphable."""

    def test_case_without_optional_entities_is_not_a_single_isolated_node(self):
        graph = _build_entity_graph(_state(_accounts_only_case()))

        assert len(graph.nodes) == 4  # customer + 3 distinct accounts
        assert len(graph.edges) == 3  # 2 transfers + 1 ownership
        assert {node.node_type for node in graph.nodes} == {"PERSON", "ACCOUNT"}

    def test_transfer_edges_carry_the_real_amount(self):
        graph = _build_entity_graph(_state(_accounts_only_case()))
        transfers = {
            (edge.source, edge.target): edge.weight
            for edge in graph.edges if edge.relationship == "SENT_TO"
        }

        assert transfers == {("ACC-SRC", "ACC-DST-1"): 48000.0, ("ACC-SRC", "ACC-DST-2"): 52500.0}

    def test_repeated_transfers_between_the_same_accounts_aggregate(self):
        """Many transfers on one pair must not draw many parallel edges."""
        case = CaseInput(transactions=[
            _txn("TXN-001", "ACC-SRC", "ACC-DST", 100.0),
            _txn("TXN-002", "ACC-SRC", "ACC-DST", 250.5),
        ])

        graph = _build_entity_graph(_state(case))
        transfers = [edge for edge in graph.edges if edge.relationship == "SENT_TO"]

        assert len(transfers) == 1
        assert transfers[0].weight == 350.5

    def test_customer_owns_the_sending_account(self):
        graph = _build_entity_graph(_state(_accounts_only_case()))

        assert any(
            edge.source == "CUST-001" and edge.target == "ACC-SRC" and edge.relationship == "OWNS"
            for edge in graph.edges
        )

    def test_accounts_are_not_duplicated_across_transactions(self):
        graph = _build_entity_graph(_state(_accounts_only_case()))
        ids = [node.node_id for node in graph.nodes]

        assert len(ids) == len(set(ids))

    def test_self_transfer_draws_no_edge(self):
        case = CaseInput(transactions=[_txn("TXN-001", "ACC-SAME", "ACC-SAME", 10.0)])

        graph = _build_entity_graph(_state(case))

        assert [node.node_id for node in graph.nodes] == ["ACC-SAME"]
        assert graph.edges == []


class TestOptionalEntities:
    """Optional records still appear — and only when the case supplies them."""

    def _full_case(self) -> CaseInput:
        return _accounts_only_case().model_copy(update={
            "merchant_info": MerchantInfo(
                merchant_id="MERCH-001", name="Test Merchant", category="Crypto",
            ),
            "beneficiary_info": BeneficiaryInfo(
                beneficiary_id="BEN-001", name="Test Beneficiary", account_number="ACC-DST-1",
            ),
            "device_info": DeviceInfo(device_id="DEV-001", device_type="MOBILE"),
        })

    def test_all_supplied_entity_types_are_present(self):
        graph = _build_entity_graph(_state(self._full_case()))

        assert {node.node_type for node in graph.nodes} == {
            "PERSON", "ACCOUNT", "MERCHANT", "BENEFICIARY", "DEVICE",
        }

    def test_beneficiary_links_to_its_own_account_when_that_account_exists(self):
        graph = _build_entity_graph(_state(self._full_case()))

        assert any(
            edge.source == "BEN-001" and edge.target == "ACC-DST-1"
            and edge.relationship == "HOLDS"
            for edge in graph.edges
        )

    def test_beneficiary_account_absent_from_the_case_draws_no_edge(self):
        """An edge is never drawn to an endpoint the case does not contain."""
        case = self._full_case().model_copy(update={
            "beneficiary_info": BeneficiaryInfo(
                beneficiary_id="BEN-001", name="Test Beneficiary",
                account_number="ACC-NOT-IN-CASE",
            ),
        })

        graph = _build_entity_graph(_state(case))

        assert "ACC-NOT-IN-CASE" not in {node.node_id for node in graph.nodes}
        assert not any(edge.relationship == "HOLDS" for edge in graph.edges)

    def test_existing_relationships_are_preserved(self):
        graph = _build_entity_graph(_state(self._full_case()))
        relationships = {
            (edge.source, edge.relationship, edge.target) for edge in graph.edges
        }

        assert ("CUST-001", "ASSOCIATED_WITH", "BEN-001") in relationships
        assert ("BEN-001", "IDENTIFIED_AS", "MERCH-001") in relationships
        assert ("CUST-001", "USED_DEVICE", "DEV-001") in relationships

    def test_no_entities_at_all_yields_an_empty_graph(self):
        """Nothing is invented for a case that carries no entities."""
        graph = _build_entity_graph(_state(CaseInput(alert_reason="Nothing attached")))

        assert graph.nodes == []
        assert graph.edges == []

    def test_device_without_an_id_is_not_graphed(self):
        case = _accounts_only_case().model_copy(update={
            "device_info": DeviceInfo(device_type="MOBILE"),
        })

        graph = _build_entity_graph(_state(case))

        assert not any(node.node_type == "DEVICE" for node in graph.nodes)


class TestGraphIntegrity:
    """Structural guarantees the frontend renderer relies on."""

    @pytest.mark.parametrize("case_builder", [
        _accounts_only_case,
        lambda: CaseInput(alert_reason="Sparse"),
    ])
    def test_every_edge_endpoint_resolves_to_a_node(self, case_builder):
        graph = _build_entity_graph(_state(case_builder()))
        node_ids = {node.node_id for node in graph.nodes}

        for edge in graph.edges:
            assert edge.source in node_ids
            assert edge.target in node_ids

    def test_graph_is_deterministic(self):
        first = _build_entity_graph(_state(_accounts_only_case()))
        second = _build_entity_graph(_state(_accounts_only_case()))

        assert first.model_dump() == second.model_dump()


class TestReasoningGraph:
    """The hypotheses -> evidence -> compliance -> decision graph.

    This graph was never broken in the backend — it was rendered collapsed by
    the frontend, which made it look like it had stopped being generated. These
    tests pin the structure so a real regression is distinguishable from that.
    """

    def _completed_state(self):
        from app.schemas.investigation_state import (
            AgentStatus,
            ComplianceMapping,
            DecisionAction,
            DecisionOptimization,
            EvidenceComplianceValidation,
            Hypothesis,
            InvestigationReasoning,
            SeverityLevel,
        )

        return _state(_accounts_only_case()).model_copy(update={
            "investigation_reasoning": InvestigationReasoning(
                status=AgentStatus.COMPLETED,
                hypotheses=[
                    Hypothesis(
                        hypothesis_id="HYP-001", title="Unauthorised use",
                        description="d", confidence=0.7,
                        supporting_evidence=["TXN-001"], contradicting_evidence=["TXN-002"],
                    ),
                ],
            ),
            "evidence_compliance_validation": EvidenceComplianceValidation(
                status=AgentStatus.COMPLETED,
                compliance_mappings=[
                    ComplianceMapping(
                        regulation_id="BSA-1020.320", regulation_name="SAR",
                        severity=SeverityLevel.HIGH, evidence_references=["TXN-001"],
                    ),
                ],
            ),
            "decision_optimization": DecisionOptimization(
                status=AgentStatus.COMPLETED,
                recommended_decision=DecisionAction.ESCALATE,
            ),
        })

    def test_all_four_layers_are_present(self):
        from app.agents.reporting_agent import _build_reasoning_graph

        graph = _build_reasoning_graph(self._completed_state())

        assert {node.node_type for node in graph.nodes} == {
            "EVIDENCE", "HYPOTHESIS", "COMPLIANCE", "DECISION",
        }

    def test_evidence_informs_hypotheses_and_supports_compliance(self):
        from app.agents.reporting_agent import _build_reasoning_graph

        graph = _build_reasoning_graph(self._completed_state())
        relationships = {(e.source, e.relationship, e.target) for e in graph.edges}

        assert ("TXN-001", "INFORMS", "HYP-001") in relationships
        assert ("TXN-002", "INFORMS", "HYP-001") in relationships
        assert ("TXN-001", "SUPPORTS", "BSA-1020.320") in relationships

    def test_hypotheses_and_compliance_feed_the_decision(self):
        from app.agents.reporting_agent import _build_reasoning_graph

        graph = _build_reasoning_graph(self._completed_state())
        relationships = {(e.source, e.relationship, e.target) for e in graph.edges}

        assert ("HYP-001", "INFORMS", "ESCALATE") in relationships
        assert ("BSA-1020.320", "INFORMS", "ESCALATE") in relationships

    def test_every_edge_endpoint_resolves_to_a_node(self):
        from app.agents.reporting_agent import _build_reasoning_graph

        graph = _build_reasoning_graph(self._completed_state())
        node_ids = {node.node_id for node in graph.nodes}

        for edge in graph.edges:
            assert edge.source in node_ids
            assert edge.target in node_ids

    def test_a_state_without_reasoning_yields_an_empty_graph(self):
        from app.agents.reporting_agent import _build_reasoning_graph

        graph = _build_reasoning_graph(_state(_accounts_only_case()))

        assert graph.nodes == []
        assert graph.edges == []
