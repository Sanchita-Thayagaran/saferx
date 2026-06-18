"""Unit tests for agent/models.py — Pydantic schema validation."""
import pytest
from pydantic import ValidationError

from agent.models import (
    ActionGuidance,
    AnomalyFlag,
    DatabaseMatch,
    ExtractedMedicineInfo,
    RegulatoryReport,
    RiskAssessment,
    RiskLevel,
    VerificationRequest,
    VerificationResponse,
)


class TestRiskLevel:
    def test_values_are_strings(self):
        assert RiskLevel.GREEN.value == "GREEN"
        assert RiskLevel.YELLOW.value == "YELLOW"
        assert RiskLevel.RED.value == "RED"

    def test_serialises_as_plain_string(self):
        assert RiskLevel.RED == "RED"


class TestVerificationRequest:
    def test_valid_request(self):
        req = VerificationRequest(input_text="Paracetamol 500mg")
        assert req.input_text == "Paracetamol 500mg"
        assert req.locale == "en"
        assert req.session_id is None

    def test_empty_input_rejected(self):
        with pytest.raises(ValidationError):
            VerificationRequest(input_text="")

    def test_oversized_input_rejected(self):
        with pytest.raises(ValidationError):
            VerificationRequest(input_text="x" * 2001)

    def test_custom_locale(self):
        req = VerificationRequest(input_text="Paracetamol", locale="fr")
        assert req.locale == "fr"

    def test_session_id_optional(self):
        req = VerificationRequest(input_text="Paracetamol", session_id="abc-123")
        assert req.session_id == "abc-123"


class TestDatabaseMatch:
    def test_confidence_in_bounds(self):
        m = DatabaseMatch(source="FDA", matched=True, confidence=0.5)
        assert 0.0 <= m.confidence <= 1.0

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            DatabaseMatch(source="FDA", matched=True, confidence=1.5)

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            DatabaseMatch(source="FDA", matched=True, confidence=-0.1)

    def test_default_confidence_is_zero(self):
        m = DatabaseMatch(source="FDA", matched=False)
        assert m.confidence == 0.0

    def test_optional_fields_default_none(self):
        m = DatabaseMatch(source="FDA", matched=False)
        assert m.record_id is None
        assert m.alert_type is None
        assert m.url is None


class TestExtractedMedicineInfo:
    def test_requires_raw_input(self):
        with pytest.raises(ValidationError):
            ExtractedMedicineInfo()

    def test_all_other_fields_optional(self):
        info = ExtractedMedicineInfo(raw_input="some text")
        assert info.drug_name is None
        assert info.batch_number is None
        assert info.manufacturer is None


class TestRiskAssessment:
    def test_flags_default_empty_list(self):
        ra = RiskAssessment(level=RiskLevel.GREEN, score=0.1, reasoning="ok")
        assert ra.flags == []
        assert ra.citations == []

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            RiskAssessment(level=RiskLevel.RED, score=1.5, reasoning="bad")


class TestActionGuidance:
    def test_emergency_defaults_false(self):
        ag = ActionGuidance(summary="ok", steps=["step1"])
        assert ag.emergency is False
        assert ag.contact_authority is None


class TestVerificationResponse:
    def _minimal_kwargs(self):
        return dict(
            request_id="req-1",
            extracted_info=ExtractedMedicineInfo(raw_input="test"),
            database_matches=[],
            risk_assessment=RiskAssessment(level=RiskLevel.GREEN, score=0.1, reasoning="ok"),
            action_guidance=ActionGuidance(summary="ok", steps=["step1"]),
            risk_level=RiskLevel.GREEN,
            verified=True,
        )

    def test_reasoning_trace_defaults_empty(self):
        resp = VerificationResponse(**self._minimal_kwargs())
        assert resp.reasoning_trace == []

    def test_disclaimer_defaults_empty_string(self):
        resp = VerificationResponse(**self._minimal_kwargs())
        assert resp.disclaimer == ""

    def test_report_defaults_none(self):
        resp = VerificationResponse(**self._minimal_kwargs())
        assert resp.report is None

    def test_timestamp_auto_populated(self):
        resp = VerificationResponse(**self._minimal_kwargs())
        assert resp.timestamp is not None
