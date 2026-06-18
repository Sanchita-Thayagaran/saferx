"""API-level tests for agent/main.py via FastAPI TestClient."""
from agent.models import RiskLevel


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "SafeRx"
        assert body["version"] == "1.0.0"


class TestRootEndpoint:
    def test_root_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "SafeRx" in resp.text


class TestVerifyEndpoint:
    def test_green_payload_returns_200(self, client, green_payload):
        resp = client.post("/verify", json=green_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["risk_level"] == RiskLevel.GREEN.value
        assert body["verified"] is True

    def test_yellow_payload_returns_200(self, client, yellow_payload):
        resp = client.post("/verify", json=yellow_payload)
        assert resp.status_code == 200
        assert resp.json()["risk_level"] == RiskLevel.YELLOW.value

    def test_red_payload_returns_200(self, client, red_payload):
        resp = client.post("/verify", json=red_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["risk_level"] == RiskLevel.RED.value
        assert body["action_guidance"]["emergency"] is True

    def test_insufficient_payload_returns_yellow_unverified(self, client, insufficient_payload):
        resp = client.post("/verify", json=insufficient_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["risk_level"] == RiskLevel.YELLOW.value
        assert body["verified"] is False

    def test_empty_input_text_returns_422(self, client):
        resp = client.post("/verify", json={"input_text": ""})
        assert resp.status_code == 422

    def test_missing_input_text_returns_422(self, client):
        resp = client.post("/verify", json={})
        assert resp.status_code == 422

    def test_oversized_input_returns_422(self, client):
        resp = client.post("/verify", json={"input_text": "x" * 2001})
        assert resp.status_code == 422

    def test_response_includes_disclaimer(self, client, green_payload):
        resp = client.post("/verify", json=green_payload)
        assert resp.json()["disclaimer"] != ""

    def test_response_includes_reasoning_trace(self, client, green_payload):
        resp = client.post("/verify", json=green_payload)
        assert len(resp.json()["reasoning_trace"]) > 0


class TestVerifyDemoEndpoint:
    def test_demo_green_scenario(self, client):
        resp = client.post("/verify/demo", params={"scenario": "green"})
        assert resp.status_code == 200
        assert resp.json()["risk_level"] == RiskLevel.GREEN.value

    def test_demo_yellow_scenario(self, client):
        resp = client.post("/verify/demo", params={"scenario": "yellow"})
        assert resp.status_code == 200
        assert resp.json()["risk_level"] == RiskLevel.YELLOW.value

    def test_demo_red_scenario(self, client):
        resp = client.post("/verify/demo", params={"scenario": "red"})
        assert resp.status_code == 200
        assert resp.json()["risk_level"] == RiskLevel.RED.value

    def test_demo_defaults_to_red(self, client):
        resp = client.post("/verify/demo")
        assert resp.status_code == 200
        assert resp.json()["risk_level"] == RiskLevel.RED.value

    def test_demo_invalid_scenario_returns_422(self, client):
        resp = client.post("/verify/demo", params={"scenario": "purple"})
        assert resp.status_code == 422
