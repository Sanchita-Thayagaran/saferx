"""
End-to-end integration tests — full pipeline from raw input text through the
HTTP API to the final VerificationResponse. These exercise the real chain
(extraction → Foundry IQ → anomaly reasoning → scoring → guidance → reporting)
in mock mode, with no internal function mocked out.
"""
from agent.models import RiskLevel


class TestFullPipelineGreen:
    def test_clean_medicine_passes_end_to_end(self, client):
        resp = client.post(
            "/verify",
            json={"input_text": "Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001"},
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["risk_level"] == RiskLevel.GREEN.value
        assert body["verified"] is True
        assert body["report"] is None
        assert body["action_guidance"]["emergency"] is False
        assert any(m["matched"] for m in body["database_matches"])


class TestFullPipelineYellow:
    def test_suspect_batch_flows_to_yellow_with_report(self, client):
        resp = client.post(
            "/verify",
            json={"input_text": "Amoxicillin 250mg suspect batch recall AMX-HOLD-99"},
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["risk_level"] == RiskLevel.YELLOW.value
        assert body["verified"] is False
        assert body["report"] is not None
        assert "report_id" in body["report"]
        assert body["action_guidance"]["contact_authority"] is not None


class TestFullPipelineRed:
    def test_counterfeit_flows_to_red_with_emergency_report(self, client):
        resp = client.post(
            "/verify",
            json={"input_text": "Artesunate 50mg fake seized counterfeit batch BX7741"},
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["risk_level"] == RiskLevel.RED.value
        assert body["verified"] is False
        assert body["action_guidance"]["emergency"] is True
        assert body["report"] is not None
        assert "CRITICAL" in body["report"]["markdown"] or "counterfeit" in body["report"]["markdown"].lower()


class TestRegressionScenarios:
    """End-to-end coverage for every bug previously reported and fixed by hand."""

    def test_yellow_and_green_are_distinguishable(self, client):
        """Bug #1: YELLOW and GREEN both said 'verified safe'."""
        green = client.post(
            "/verify", json={"input_text": "Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001"}
        ).json()
        yellow = client.post(
            "/verify", json={"input_text": "Amoxicillin 250mg suspect batch recall AMX-HOLD-99"}
        ).json()
        assert green["risk_level"] != yellow["risk_level"]
        assert green["verified"] is True
        assert yellow["verified"] is False

    def test_yellow_scenario_does_not_escalate_to_red(self, client):
        """Bug #2: YELLOW scenario regressed to RED after the first fix."""
        resp = client.post(
            "/verify", json={"input_text": "Amoxicillin 250mg suspect batch recall AMX-HOLD-99"}
        )
        assert resp.json()["risk_level"] == RiskLevel.YELLOW.value

    def test_manufactured_substring_does_not_trigger_red(self, client):
        """Bug #3: 'manufactured' contains 'red' as a substring and falsely triggered RED."""
        resp = client.post(
            "/verify",
            json={
                "input_text": (
                    "Paracetamol 500mg tablets, GlaxoSmithKline, "
                    "batch GSK-2025-441, manufactured UK"
                )
            },
        )
        assert resp.json()["risk_level"] != RiskLevel.RED.value

    def test_nonsense_input_is_not_verified_safe(self, client):
        """Bug #4: typing 'papa' returned VERIFIED SAFE."""
        resp = client.post("/verify", json={"input_text": "papa"})
        body = resp.json()
        assert body["verified"] is False
        assert body["risk_level"] != RiskLevel.GREEN.value


class TestSessionAndLocale:
    def test_session_id_is_echoed_back(self, client):
        resp = client.post(
            "/verify",
            json={"input_text": "Paracetamol 500mg GlaxoSmithKline", "session_id": "sess-42"},
        )
        assert resp.json()["session_id"] == "sess-42"

    def test_locale_passed_through_without_error(self, client):
        resp = client.post(
            "/verify",
            json={"input_text": "Paracetamol 500mg GlaxoSmithKline", "locale": "fr"},
        )
        assert resp.status_code == 200


class TestProcessingTime:
    def test_processing_time_is_recorded(self, client, green_payload):
        resp = client.post("/verify", json=green_payload)
        assert resp.json()["processing_time_ms"] >= 0

    def test_each_request_gets_unique_request_id(self, client, green_payload):
        r1 = client.post("/verify", json=green_payload).json()
        r2 = client.post("/verify", json=green_payload).json()
        assert r1["request_id"] != r2["request_id"]
