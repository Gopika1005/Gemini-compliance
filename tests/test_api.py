"""API-related tests for the Gemini Compliance Monitor."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    # Force mock mode by setting the placeholder API key
    monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    return


def test_root_and_health():
    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "operational"

        r2 = client.get("/health")
        assert r2.status_code == 200
        assert "service" in r2.json()


def test_regulations():
    with TestClient(app) as client:
        r = client.get("/regulations")
        assert r.status_code == 200
        payload = r.json()
        assert "regulations" in payload
        assert "GDPR" in payload["regulations"]


def test_quick_check():
    with TestClient(app) as client:
        r = client.post("/quick-check", params={"company_name": "TestCo"})
        assert r.status_code == 200
        data = r.json()
        assert "compliance_score" in data
        assert "violations" in data
        assert "risk_level" in data
