import asyncio

from src.audit_system import SystemAuditor


def test_audit_gdpr_rules():
    auditor = SystemAuditor()
    company_data = {
        "company_name": "TestCo",
        "data_collected": list(range(12)),  # >10 to trigger data_minimization
        "data_storage_location": "Global",
        "ai_models_used": [],
        "user_count": 1000,
    }

    results = asyncio.run(auditor.audit_systems(company_data, ["GDPR"]))
    violations = results.get("violations", [])
    ids = {v.get("id") for v in violations}

    assert "gdpr_data_minimization" in ids
    assert "gdpr_international_transfer" in ids


def test_audit_ccpa_and_ai_act_rules():
    auditor = SystemAuditor()

    # CCPA threshold
    c_data = {
        "user_count": 60000,
        "data_collected": [],
        "data_storage_location": "US",
        "ai_models_used": [],
    }
    c_res = asyncio.run(auditor.audit_systems(c_data, ["CCPA"]))
    c_ids = {v.get("id") for v in c_res.get("violations", [])}
    assert "ccpa_threshold" in c_ids

    # AI Act
    a_data = {
        "user_count": 500,
        "data_collected": [],
        "data_storage_location": "EU",
        "ai_models_used": ["custom"],
    }
    a_res = asyncio.run(auditor.audit_systems(a_data, ["AI_ACT"]))
    a_ids = {v.get("id") for v in a_res.get("violations", [])}
    assert "aia_transparency" in a_ids
