"""Regression tests for Reasoning Agent grounding validation.

Tests that _check_grounding_violation correctly:
1. REJECTS hypotheses that reference data categories the pipeline never
   supplies (biometric, facial, KYC, passport, demographic, invoice,
   past behavior, previous transaction).
2. ACCEPTS hypotheses that use generic descriptive words (device, channel,
   mobile, document, alert, profile, history) because these are natural
   language Gemini uses when describing facts present in the prompt.
3. ACCEPTS hypotheses that reference concrete values present in
   available_text (transaction IDs, amounts, customer names, anomaly
   descriptions).
4. Verifies that _normalise_hypotheses strips invented concrete IDs
   (the separate layer of protection via _evidence_is_available).
5. Verifies _available_evidence_values returns the expected set.
"""

from datetime import datetime

import pytest

from app.agents.reasoning_agent import (
    _available_evidence_values,
    _check_grounding_violation,
    _normalise_hypotheses,
)
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    CaseInput,
    ContextIntelligence,
    CustomerProfile,
    DetectedAnomaly,
    DeviceInfo,
    Hypothesis,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Fixtures ────────────────────────────────────────────────────────────


def _realistic_state():
    """Build the same case structure used in the real pipeline smoke test."""
    case_input = CaseInput(
        alert_reason=(
            "Large wire transfer to a first-time beneficiary in a high-risk "
            "jurisdiction, initiated from an unknown device with geolocation "
            "mismatch (device in Romania, customer based in New York)."
        ),
        customer_profile=CustomerProfile(
            customer_id="CUST-90215",
            name="James Whitfield",
            email="j.whitfield@email.com",
            phone="+1-212-555-0173",
            address="350 Park Avenue, New York, NY 10022",
            date_of_birth="1983-04-12",
            account_open_date="2019-06-15",
            risk_rating="MEDIUM",
            occupation="Portfolio Manager",
            nationality="US",
        ),
        merchant_info=MerchantInfo(
            merchant_id="MERCH-KY-7741",
            name="CryptoVault Holdings Ltd.",
            category="Cryptocurrency Exchange",
            country="KY",
            risk_level=SeverityLevel.HIGH,
            registered_date="2023-01-20",
        ),
        device_info=DeviceInfo(
            device_id="DEV-UNKNOWN-8812",
            device_type="MOBILE",
            ip_address="185.220.101.34",
            geolocation="Bucharest, Romania",
            is_known_device=False,
            os="Android 14",
            browser="Chrome Mobile 126",
        ),
        transactions=[
            Transaction(
                transaction_id="TXN-2025-0819-00347",
                amount=48500.0,
                currency="USD",
                timestamp=datetime(2025, 8, 19, 14, 32, 11),
                sender_account="ACC-US-8821004",
                receiver_account="ACC-KY-5529183",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Investment deposit - CryptoVault Holdings",
                location="New York, US",
            ),
        ],
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-2025-0441",
                document_type="BANK_STATEMENT",
                file_name="whitfield_aug2025_statement.pdf",
                uploaded_at=datetime(2025, 8, 19, 15, 0, 0),
                summary="Monthly statement showing irregular outbound transfers.",
            ),
        ],
    )
    state = create_initial_state("CASE-GROUND-001", case_input)
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary=(
                "James Whitfield has 1 transaction(s) totalling $48,500.00 "
                "under investigation."
            ),
            key_indicators=[
                "1 large transaction(s) exceeding $10,000.00",
                "Largest single transaction: $48,500.00",
            ],
            anomalies=[
                DetectedAnomaly(
                    anomaly_id="ANOM-001",
                    anomaly_type=AnomalyType.POINT,
                    severity=SeverityLevel.HIGH,
                    description=(
                        "Large WIRE transaction of $48,500.00 exceeds "
                        "$10,000.00 threshold."
                    ),
                    related_transactions=["TXN-2025-0819-00347"],
                ),
            ],
            risk_score=0.62,
        ),
    })


# ── Test: _available_evidence_values returns expected strict set ──────


class TestAvailableEvidenceValues:
    """Verify that _available_evidence_values includes ONLY the fields the
    strict implementation collects: transaction IDs, descriptions, accounts,
    document IDs/types/summaries, customer profile values, alert_reason,
    context intelligence indicators/summaries/anomalies.

    It includes device IDs so concrete device evidence can be checked, but
    does not include the remaining device fields, merchant fields,
    beneficiary fields, or transaction channel/type/location.
    """

    @pytest.fixture()
    def values(self):
        return _available_evidence_values(_realistic_state())

    @pytest.fixture()
    def values_text(self, values):
        return " ".join(v.lower() for v in values)

    # --- Included: transaction core fields ---

    def test_includes_transaction_id(self, values):
        assert any("TXN-2025-0819-00347" in v for v in values)

    def test_includes_sender_account(self, values):
        assert any("ACC-US-8821004" in v for v in values)

    def test_includes_receiver_account(self, values):
        assert any("ACC-KY-5529183" in v for v in values)

    def test_includes_description(self, values):
        assert any("CryptoVault" in v for v in values)

    # --- Included: document fields ---

    def test_includes_document_id(self, values):
        assert "DOC-2025-0441" in values

    def test_includes_document_type(self, values):
        assert "BANK_STATEMENT" in values

    def test_includes_document_summary(self, values):
        assert any("irregular outbound" in v for v in values)

    # --- Included: customer profile (via model_dump) ---

    def test_includes_customer_id(self, values):
        assert "CUST-90215" in values

    def test_includes_customer_name(self, values):
        assert "James Whitfield" in values

    # --- Included: alert_reason ---

    def test_includes_alert_reason(self, values):
        assert any("wire transfer" in v.lower() for v in values)

    # --- Included: context intelligence ---

    def test_includes_anomaly_id(self, values):
        assert "ANOM-001" in values

    def test_includes_anomaly_description(self, values):
        assert any("$48,500.00 exceeds" in v for v in values)

    def test_includes_context_summary(self, values):
        assert any("totalling $48,500.00" in v for v in values)

    def test_includes_key_indicators(self, values):
        assert any("$10,000.00" in v for v in values)

    # --- NOT included: device, merchant, beneficiary, channel, type, location ---

    def test_includes_device_id(self, values):
        assert "DEV-UNKNOWN-8812" in values

    def test_does_not_include_device_type(self, values):
        assert "MOBILE" not in values

    def test_does_not_include_geolocation(self, values):
        assert "Bucharest, Romania" not in values

    def test_does_not_include_merchant_id(self, values):
        assert "MERCH-KY-7741" not in values

    def test_does_not_include_transaction_type(self, values):
        assert "WIRE" not in values

    def test_does_not_include_channel(self, values):
        assert "ONLINE" not in values


# ── Test: grounding REJECTS never-supplied data categories ───────────


class TestGroundingRejectsNeverSuppliedCategories:
    """These data categories are NEVER supplied by the pipeline and should
    always be rejected by _check_grounding_violation."""

    def test_rejects_biometric_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Biometric Verification Failure",
            description="The biometric verification failed for this customer.",
            confidence=0.8,
            supporting_evidence=["Biometric mismatch detected"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "biometric" in result.lower()

    def test_rejects_facial_recognition_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Identity Fraud via Facial Mismatch",
            description="Facial recognition shows a mismatch.",
            confidence=0.7,
            supporting_evidence=["Facial scan did not match"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "face" in result.lower() or "facial" in result.lower()

    def test_rejects_kyc_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="KYC Deficiency",
            description="The KYC process was incomplete.",
            confidence=0.6,
            supporting_evidence=["KYC documents missing"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "kyc" in result.lower()

    def test_rejects_passport_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Stolen Passport",
            description="A stolen passport was used to open this account.",
            confidence=0.5,
            supporting_evidence=["Passport forgery detected"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "passport" in result.lower()

    def test_rejects_demographic_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Demographic Anomaly",
            description="The demographic data suggests an anomaly.",
            confidence=0.4,
            supporting_evidence=["Demographic data suggests anomaly"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "demographic" in result.lower()

    def test_rejects_invoice_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Invoice Fraud",
            description="The invoice was forged to justify the transfer.",
            confidence=0.4,
            supporting_evidence=["Forged invoice detected"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "invoice" in result.lower()

    def test_rejects_past_behavior_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Behavioural Change",
            description="The customer's past behavior suggests this is unusual.",
            confidence=0.5,
            supporting_evidence=["Past behavior analysis"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "past behavior" in result.lower()

    def test_rejects_previous_transaction_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Pattern Analysis",
            description="A previous transaction shows the same pattern.",
            confidence=0.5,
            supporting_evidence=["Previous transaction to same recipient"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "previous transaction" in result.lower()

    def test_rejects_id_card_reference(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Forged Identity",
            description="The id card was forged.",
            confidence=0.5,
            supporting_evidence=["Forged id card detected"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is not None
        assert "id card" in result.lower()


# ── Test: grounding ACCEPTS generic descriptive language ─────────────


class TestGroundingAcceptsGenericDescriptiveLanguage:
    """Generic words like 'device', 'channel', 'mobile', 'document',
    'alert', 'profile', 'history' are NOT forbidden — they are natural
    language the LLM uses when describing facts present in the prompt.

    This is the exact regression test for the Gemini false-rejection bug.
    """

    def test_accepts_mobile_device_reference(self):
        """Gemini says 'mobile device' — should pass."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Account Takeover via Compromised Mobile Device",
            description=(
                "The $48,500.00 transfer TXN-2025-0819-00347 was initiated "
                "from an unknown mobile device in Bucharest, Romania."
            ),
            confidence=0.65,
            supporting_evidence=[
                "TXN-2025-0819-00347: $48,500.00 to ACC-KY-5529183",
                "Unknown mobile device DEV-UNKNOWN-8812",
            ],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_online_channel_reference(self):
        """Gemini says 'online channel' — should pass."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Suspicious Wire via Online Channel",
            description="The wire transfer was initiated via the online channel.",
            confidence=0.5,
            supporting_evidence=["TXN-2025-0819-00347 sent via ONLINE channel"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_document_reference(self):
        """Gemini says 'bank statement document' — should pass."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Irregular Transfer Pattern",
            description=(
                "The bank statement document DOC-2025-0441 shows irregular "
                "outbound transfers."
            ),
            confidence=0.55,
            supporting_evidence=["DOC-2025-0441: Monthly statement."],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_alert_reference(self):
        """Gemini says 'the alert was triggered' — should pass."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Alert-Driven Investigation",
            description=(
                "The alert was triggered by a large wire transfer to a "
                "first-time beneficiary in a high-risk jurisdiction."
            ),
            confidence=0.6,
            supporting_evidence=["Alert triggered for geolocation mismatch"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_profile_reference(self):
        """Gemini says 'customer profile' — should pass."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Profile Consistency Check",
            description="The customer profile is consistent with the transaction.",
            confidence=0.4,
            supporting_evidence=["TXN-2025-0819-00347"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_history_reference(self):
        """Gemini says 'history' — should pass (generic word)."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Transaction History Review",
            description="The history of transfers from ACC-US-8821004 is relevant.",
            confidence=0.4,
            supporting_evidence=["TXN-2025-0819-00347"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_web_and_ip_reference(self):
        """Gemini says 'web' or 'ip address' — should pass (generic words)."""
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="IP Address Analysis",
            description="The IP address and web session suggest VPN usage.",
            confidence=0.4,
            supporting_evidence=["TXN-2025-0819-00347"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"


# ── Test: grounding ACCEPTS concrete grounded claims ─────────────────


class TestGroundingAcceptsGroundedClaims:
    """Hypotheses using concrete values from available_text should pass."""

    def test_accepts_transaction_id_and_amount(self):
        state = _realistic_state()
        hypotheses = [Hypothesis(
            hypothesis_id="HYP-001",
            title="Suspicious Wire Transfer",
            description=(
                "A $48,500.00 transfer TXN-2025-0819-00347 was sent from "
                "ACC-US-8821004 to ACC-KY-5529183."
            ),
            confidence=0.7,
            supporting_evidence=["TXN-2025-0819-00347"],
            contradicting_evidence=[],
        )]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"

    def test_accepts_clean_hypothesis_pair(self):
        state = _realistic_state()
        hypotheses = [
            Hypothesis(
                hypothesis_id="HYP-001",
                title="Potential Money Laundering",
                description=(
                    "TXN-2025-0819-00347 for $48,500.00 from ACC-US-8821004 "
                    "to ACC-KY-5529183 exceeds the $10,000.00 threshold "
                    "identified in ANOM-001."
                ),
                confidence=0.55,
                supporting_evidence=["TXN-2025-0819-00347", "ANOM-001"],
                contradicting_evidence=[],
            ),
            Hypothesis(
                hypothesis_id="HYP-002",
                title="Authorized Investment",
                description=(
                    "James Whitfield is a Portfolio Manager. The transfer "
                    "of $48,500.00 described as Investment deposit - CryptoVault "
                    "Holdings may be a legitimate investment."
                ),
                confidence=0.4,
                supporting_evidence=["TXN-2025-0819-00347"],
                contradicting_evidence=[],
            ),
        ]
        result = _check_grounding_violation(hypotheses, state)
        assert result is None, f"Should accept but got: {result}"


# ── Test: _normalise_hypotheses strips INVENTED concrete IDs ─────────


class TestNormaliseStripsInventedIDs:
    """_normalise_hypotheses (via _evidence_is_available) strips evidence
    items that reference concrete IDs not present in the state.  This is
    the separate protection layer for invented factual claims.
    """

    def test_strips_invented_transaction_id(self):
        """Evidence citing TXN-FAKE-999 should be removed."""
        state = _realistic_state()
        hyp = Hypothesis(
            hypothesis_id="HYP-001",
            title="Suspicious Transfer",
            description="A suspicious transfer was identified.",
            confidence=0.5,
            supporting_evidence=[
                "TXN-2025-0819-00347: $48,500.00",       # real — kept
                "TXN-FAKE-999: $1,000,000.00 to ACC-XX",  # invented — stripped
            ],
            contradicting_evidence=[],
        )
        normalised = _normalise_hypotheses([hyp], state)
        assert len(normalised) == 1
        assert len(normalised[0].supporting_evidence) == 1
        assert "TXN-2025-0819-00347" in normalised[0].supporting_evidence[0]

    def test_strips_invented_document_id(self):
        """Evidence citing DOC-FAKE-001 should be removed."""
        state = _realistic_state()
        hyp = Hypothesis(
            hypothesis_id="HYP-001",
            title="Document Review",
            description="Document review was conducted.",
            confidence=0.5,
            supporting_evidence=[
                "DOC-2025-0441: Monthly statement",  # real — kept
                "DOC-FAKE-001: Forged invoice",        # invented — stripped
            ],
            contradicting_evidence=[],
        )
        normalised = _normalise_hypotheses([hyp], state)
        assert len(normalised) == 1
        assert len(normalised[0].supporting_evidence) == 1
        assert "DOC-2025-0441" in normalised[0].supporting_evidence[0]

    def test_strips_invented_account_id(self):
        """Evidence citing ACC-FAKE-XYZ should be removed."""
        state = _realistic_state()
        hyp = Hypothesis(
            hypothesis_id="HYP-001",
            title="Account Analysis",
            description="Account analysis was conducted.",
            confidence=0.5,
            supporting_evidence=[
                "TXN-2025-0819-00347 from ACC-US-8821004",  # real — kept
                "ACC-FAKE-XYZ received $500,000",             # invented — stripped
            ],
            contradicting_evidence=[],
        )
        normalised = _normalise_hypotheses([hyp], state)
        assert len(normalised) == 1
        assert len(normalised[0].supporting_evidence) == 1
        assert "ACC-US-8821004" in normalised[0].supporting_evidence[0]

    def test_strips_invented_device_id(self):
        """Evidence citing DEV-FAKE-999 should be removed."""
        state = _realistic_state()
        hyp = Hypothesis(
            hypothesis_id="HYP-001",
            title="Device Analysis",
            description="Device activity was reviewed.",
            confidence=0.5,
            supporting_evidence=[
                "DEV-UNKNOWN-8812: unknown mobile device",
                "DEV-FAKE-999: known device",
            ],
            contradicting_evidence=[],
        )
        normalised = _normalise_hypotheses([hyp], state)
        assert normalised[0].supporting_evidence == [
            "DEV-UNKNOWN-8812: unknown mobile device"
        ]

    def test_keeps_all_real_ids(self):
        """Evidence citing only real IDs should be fully preserved."""
        state = _realistic_state()
        hyp = Hypothesis(
            hypothesis_id="HYP-001",
            title="Full Evidence",
            description="Complete evidence review.",
            confidence=0.6,
            supporting_evidence=[
                "TXN-2025-0819-00347: $48,500.00 from ACC-US-8821004 to ACC-KY-5529183",
                "DOC-2025-0441: Monthly statement showing irregular outbound transfers.",
            ],
            contradicting_evidence=[
                "ANOM-001: threshold breach",
            ],
        )
        normalised = _normalise_hypotheses([hyp], state)
        assert len(normalised) == 1
        assert len(normalised[0].supporting_evidence) == 2
        assert len(normalised[0].contradicting_evidence) == 1
