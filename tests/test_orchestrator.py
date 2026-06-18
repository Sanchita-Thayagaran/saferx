"""Unit tests for agent/orchestrator.py — scoring, escalation, and the full chain."""
from unittest.mock import AsyncMock

import pytest

from agent.models import DatabaseMatch, RiskLevel, VerificationRequest
from agent.orchestrator import (
    VerificationOrchestrator,
    _is_sufficient_input,
    _safety_escalate,
    _score_to_level,
)


class TestScoreToLevel:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.0, RiskLevel.GREEN),
            (0.39, RiskLevel.GREEN),
            (0.4, RiskLevel.YELLOW),
            (0.69, RiskLevel.YELLOW),
            (0.7, RiskLevel.RED),
            (1.0, RiskLevel.RED),
        ],
    )
    def test_thresholds(self, score, expected):
        assert _score_to_level(score) == expected


class TestSafetyEscalate:
    def test_critical_alert_forces_red(self, critical_matches):
        assert _safety_escalate(RiskLevel.GREEN, critical_matches) == RiskLevel.RED

    def test_investigative_alert_floors_to_yellow_not_red(self, investigative_matches):
        """Regression: 2+ flagged matches must not blindly escalate to RED."""
        assert _safety_escalate(RiskLevel.GREEN, investigative_matches) == RiskLevel.YELLOW

    def test_investigative_alert_keeps_yellow_if_already_yellow(self, investigative_matches):
        assert _safety_escalate(RiskLevel.YELLOW, investigative_matches) == RiskLevel.YELLOW

    def test_clean_matches_no_escalation(self, clean_matches):
        assert _safety_escalate(RiskLevel.GREEN, clean_matches) == RiskLevel.GREEN

    def test_red_never_downgraded(self, clean_matches):
        assert _safety_escalate(RiskLevel.RED, clean_matches) == RiskLevel.RED

    def test_critical_alert_overrides_existing_yellow(self, critical_matches):
        assert _safety_escalate(RiskLevel.YELLOW, critical_matches) == RiskLevel.RED


class TestIsSufficientInput:
    def test_single_word_rejected(self):
        assert _is_sufficient_input("papa") is False

    def test_two_short_words_rejected(self):
        assert _is_sufficient_input("ok hi") is False

    def test_word_with_four_plus_letters_accepted(self):
        assert _is_sufficient_input("take this") is True

    def test_realistic_input_accepted(self):
        assert _is_sufficient_input("Paracetamol 500mg GlaxoSmithKline") is True

    def test_empty_string_rejected(self):
        assert _is_sufficient_input("") is False

    def test_numbers_only_rejected(self):
        assert _is_sufficient_input("123 456") is False


class TestOrchestratorVerify:
    @pytest.fixture
    def orchestrator(self):
        return VerificationOrchestrator()

    @pytest.mark.asyncio
    async def test_green_scenario(self, orchestrator, green_payload):
        request = VerificationRequest(**green_payload)
        response = await orchestrator.verify(request)
        assert response.risk_level == RiskLevel.GREEN
        assert response.verified is True
        assert response.report is None

    @pytest.mark.asyncio
    async def test_yellow_scenario(self, orchestrator, yellow_payload):
        request = VerificationRequest(**yellow_payload)
        response = await orchestrator.verify(request)
        assert response.risk_level == RiskLevel.YELLOW
        assert response.verified is False
        assert response.report is not None

    @pytest.mark.asyncio
    async def test_red_scenario(self, orchestrator, red_payload):
        request = VerificationRequest(**red_payload)
        response = await orchestrator.verify(request)
        assert response.risk_level == RiskLevel.RED
        assert response.verified is False
        assert response.action_guidance.emergency is True
        assert response.report is not None

    @pytest.mark.asyncio
    async def test_insufficient_input_returns_yellow_unverified(self, orchestrator, insufficient_payload):
        """Regression: 'papa' previously returned VERIFIED SAFE."""
        request = VerificationRequest(**insufficient_payload)
        response = await orchestrator.verify(request)
        assert response.risk_level == RiskLevel.YELLOW
        assert response.verified is False
        assert response.database_matches == []

    @pytest.mark.asyncio
    async def test_manufactured_does_not_escalate_to_red(self, orchestrator, manufactured_payload):
        """Regression: 'manufactured' contains substring 'red' — must not trigger RED."""
        request = VerificationRequest(**manufactured_payload)
        response = await orchestrator.verify(request)
        assert response.risk_level != RiskLevel.RED

    @pytest.mark.asyncio
    async def test_reasoning_trace_populated(self, orchestrator, green_payload):
        request = VerificationRequest(**green_payload)
        response = await orchestrator.verify(request)
        assert len(response.reasoning_trace) >= 5
        assert any("Step 1" in step for step in response.reasoning_trace)

    @pytest.mark.asyncio
    async def test_disclaimer_always_present(self, orchestrator, green_payload):
        request = VerificationRequest(**green_payload)
        response = await orchestrator.verify(request)
        assert response.disclaimer != ""

    @pytest.mark.asyncio
    async def test_request_id_is_unique_per_call(self, orchestrator, green_payload):
        request = VerificationRequest(**green_payload)
        r1 = await orchestrator.verify(request)
        r2 = await orchestrator.verify(request)
        assert r1.request_id != r2.request_id


class TestUseRealDataFlag:
    """USE_REAL_DATA defaults to 'true' in production; here we drive it explicitly
    via the instance flag and mock both data sources to stay network-free."""

    def _orchestrator_with_mocks(self, real_matches, foundry_matches):
        orchestrator = VerificationOrchestrator()
        orchestrator.real_data_client.verify_drug_realworld = AsyncMock(
            return_value={"matches": real_matches, "sources_checked": [], "real_data": True, "query_count": 2}
        )
        orchestrator._iq.verify_drug = AsyncMock(return_value=foundry_matches)
        return orchestrator

    @pytest.mark.asyncio
    async def test_real_data_true_merges_both_sources(self, green_payload):
        real_matches = [DatabaseMatch(source="FDA_ENFORCEMENT", matched=True, alert_type=None, confidence=0.5)]
        foundry_matches = [DatabaseMatch(source="WHO_GFMD", matched=True, alert_type=None, confidence=0.97)]
        orchestrator = self._orchestrator_with_mocks(real_matches, foundry_matches)
        orchestrator.use_real_data = True

        response = await orchestrator.verify(VerificationRequest(**green_payload))

        orchestrator.real_data_client.verify_drug_realworld.assert_awaited_once()
        orchestrator._iq.verify_drug.assert_awaited_once()
        sources = {m.source for m in response.database_matches}
        assert sources == {"FDA_ENFORCEMENT", "WHO_GFMD"}

    @pytest.mark.asyncio
    async def test_real_data_false_skips_real_data_client(self, green_payload):
        real_matches = [DatabaseMatch(source="FDA_ENFORCEMENT", matched=True, alert_type=None, confidence=0.5)]
        foundry_matches = [DatabaseMatch(source="WHO_GFMD", matched=True, alert_type=None, confidence=0.97)]
        orchestrator = self._orchestrator_with_mocks(real_matches, foundry_matches)
        orchestrator.use_real_data = False

        response = await orchestrator.verify(VerificationRequest(**green_payload))

        orchestrator.real_data_client.verify_drug_realworld.assert_not_awaited()
        orchestrator._iq.verify_drug.assert_awaited_once()
        sources = {m.source for m in response.database_matches}
        assert sources == {"WHO_GFMD"}

    def test_default_flag_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("USE_REAL_DATA", "false")
        assert VerificationOrchestrator().use_real_data is False
        monkeypatch.setenv("USE_REAL_DATA", "true")
        assert VerificationOrchestrator().use_real_data is True
