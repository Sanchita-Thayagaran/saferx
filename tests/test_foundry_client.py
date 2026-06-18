"""Unit tests for agent/foundry_client.py — mock-mode client behaviour."""
import pytest

from agent.foundry_client import (
    MOCK_MODE,
    FoundryAgentClient,
    FoundryIQClient,
    _mock_matches_for,
)


def test_mock_mode_active_for_tests():
    assert MOCK_MODE is True, "Tests expect MOCK_MODE — unset Azure env vars before running pytest"


class TestMockMatchesFor:
    def test_red_keywords(self):
        for text in ["fake medicine", "counterfeit batch", "seized shipment", "BX7741"]:
            matches = _mock_matches_for(text, None)
            assert any(m.alert_type == "COUNTERFEIT_CONFIRMED" for m in matches)

    def test_yellow_keywords(self):
        for text in ["suspect quality", "recall notice", "on hold", "query raised"]:
            matches = _mock_matches_for(text, None)
            assert any(m.alert_type == "SUSPECT_QUALITY" for m in matches)

    def test_green_fallback(self):
        matches = _mock_matches_for("Paracetamol GlaxoSmithKline", None)
        assert all(m.alert_type is None for m in matches if m.matched)

    def test_manufactured_does_not_trigger_red(self):
        """Regression: 'manufactured' contains substring 'red' — must not match RED via substring."""
        matches = _mock_matches_for("Paracetamol manufactured UK", None)
        assert not any(m.alert_type == "COUNTERFEIT_CONFIRMED" for m in matches)

    def test_word_boundary_on_batch_number(self):
        matches = _mock_matches_for("Amoxicillin", "BX7741")
        assert any(m.alert_type == "COUNTERFEIT_CONFIRMED" for m in matches)

    def test_shredded_does_not_trigger_red_via_substring(self):
        """'red' should not match inside unrelated words like 'shredded'."""
        matches = _mock_matches_for("shredded packaging", None)
        assert all(m.alert_type is None for m in matches if m.matched)


class TestFoundryIQClientMock:
    @pytest.mark.asyncio
    async def test_verify_drug_uses_raw_input_over_drug_name(self):
        """Regression: extracted drug_name lost YELLOW keywords present in raw_input."""
        client = FoundryIQClient()
        matches = await client.verify_drug(
            drug_name="Amoxicillin",
            batch_number=None,
            raw_input="Amoxicillin 250mg suspect batch recall AMX-HOLD-99",
        )
        assert any(m.alert_type == "SUSPECT_QUALITY" for m in matches)

    @pytest.mark.asyncio
    async def test_verify_drug_falls_back_to_drug_name_without_raw_input(self):
        client = FoundryIQClient()
        matches = await client.verify_drug(drug_name="counterfeit", batch_number=None)
        assert any(m.alert_type == "COUNTERFEIT_CONFIRMED" for m in matches)

    @pytest.mark.asyncio
    async def test_returns_five_sources(self):
        client = FoundryIQClient()
        matches = await client.verify_drug(drug_name="Paracetamol", batch_number=None)
        sources = {m.source for m in matches}
        assert sources == {"WHO_GFMD", "FDA", "EMA", "REGIONAL", "BATCH_ALERTS"}


class TestFoundryAgentClientMock:
    @pytest.mark.asyncio
    async def test_extract_medicine_info_finds_batch_number(self):
        """Batch regex requires exactly 2 uppercase letters + 4+ digits + optional letter."""
        client = FoundryAgentClient()
        info = await client.extract_medicine_info("Paracetamol 500mg batch PA2024A")
        assert info.batch_number == "PA2024A"

    @pytest.mark.asyncio
    async def test_extract_medicine_info_sets_raw_input(self):
        client = FoundryAgentClient()
        raw = "Paracetamol 500mg GlaxoSmithKline"
        info = await client.extract_medicine_info(raw)
        assert info.raw_input == raw

    @pytest.mark.asyncio
    async def test_assess_anomalies_red_for_critical_alert(self):
        from agent.models import ExtractedMedicineInfo

        client = FoundryAgentClient()
        matches = _mock_matches_for("counterfeit", None)
        info = ExtractedMedicineInfo(raw_input="counterfeit")
        assessment = await client.assess_anomalies(info, matches)
        assert assessment.score >= 0.7

    @pytest.mark.asyncio
    async def test_assess_anomalies_low_score_for_clean_matches(self):
        from agent.models import ExtractedMedicineInfo

        client = FoundryAgentClient()
        matches = _mock_matches_for("Paracetamol GlaxoSmithKline", None)
        info = ExtractedMedicineInfo(raw_input="Paracetamol GlaxoSmithKline")
        assessment = await client.assess_anomalies(info, matches)
        assert assessment.score < 0.4

    @pytest.mark.asyncio
    async def test_generate_action_guidance_emergency_for_red(self):
        from agent.models import RiskAssessment, RiskLevel

        client = FoundryAgentClient()
        ra = RiskAssessment(level=RiskLevel.RED, score=0.9, reasoning="counterfeit confirmed")
        guidance = await client.generate_action_guidance(ra, language="en")
        assert guidance.emergency is True

    @pytest.mark.asyncio
    async def test_generate_action_guidance_not_emergency_for_green(self):
        from agent.models import RiskAssessment, RiskLevel

        client = FoundryAgentClient()
        ra = RiskAssessment(level=RiskLevel.GREEN, score=0.1, reasoning="clean")
        guidance = await client.generate_action_guidance(ra, language="en")
        assert guidance.emergency is False
