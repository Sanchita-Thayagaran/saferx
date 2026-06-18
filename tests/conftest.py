import os

# Tests must stay fast, deterministic, and network-free — force mock data even
# though VerificationOrchestrator defaults USE_REAL_DATA to "true" in production.
# Must be set before agent.main / VerificationOrchestrator is imported/instantiated.
os.environ["USE_REAL_DATA"] = "false"

import pytest
from fastapi.testclient import TestClient

from agent.foundry_client import MOCK_MODE
from agent.main import app
from agent.models import DatabaseMatch, RiskLevel


# ── Sanity guard ──────────────────────────────────────────────────────────────

def pytest_configure(config):
    if not MOCK_MODE:
        import warnings
        warnings.warn(
            "MOCK_MODE is False — tests may make real Azure API calls. "
            "Unset AZURE_FOUNDRY_API_KEY and AZURE_SEARCH_API_KEY to run in mock mode.",
            UserWarning,
            stacklevel=2,
        )


# ── App client ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── Request payloads ──────────────────────────────────────────────────────────

@pytest.fixture
def green_payload():
    return {"input_text": "Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001", "locale": "en"}

@pytest.fixture
def yellow_payload():
    return {"input_text": "Amoxicillin 250mg suspect batch recall AMX-HOLD-99", "locale": "en"}

@pytest.fixture
def red_payload():
    return {"input_text": "Artesunate 50mg fake seized counterfeit batch BX7741", "locale": "en"}

@pytest.fixture
def insufficient_payload():
    return {"input_text": "papa", "locale": "en"}

@pytest.fixture
def manufactured_payload():
    # regression: "manufactured" contains "red" as substring — must not trigger RED
    return {"input_text": "Paracetamol 500mg tablets manufactured UK batch GSK-2025-441", "locale": "en"}


# ── Database match helpers ────────────────────────────────────────────────────

@pytest.fixture
def critical_matches():
    return [
        DatabaseMatch(source="WHO_GFMD", matched=True, alert_type="COUNTERFEIT_CONFIRMED", confidence=0.99),
        DatabaseMatch(source="FDA",      matched=True, alert_type="CLASS_I_RECALL",        confidence=0.98),
    ]

@pytest.fixture
def investigative_matches():
    return [
        DatabaseMatch(source="WHO_GFMD", matched=True, alert_type="SUSPECT_QUALITY",      confidence=0.82),
        DatabaseMatch(source="REGIONAL", matched=True, alert_type="UNDER_INVESTIGATION",  confidence=0.74),
    ]

@pytest.fixture
def clean_matches():
    return [
        DatabaseMatch(source="WHO_GFMD", matched=True,  alert_type=None, confidence=0.97),
        DatabaseMatch(source="FDA",      matched=True,  alert_type=None, confidence=0.95),
        DatabaseMatch(source="EMA",      matched=False, confidence=0.0),
    ]
