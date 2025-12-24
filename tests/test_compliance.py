"""Unit tests for the compliance analysis pipeline."""

import asyncio
from src.compliance_monitor import ComplianceMonitor
from src.regulation_parser import RegulationParser
from src.audit_system import SystemAuditor
from src.fix_suggester import FixSuggester


def test_compliance_monitor_pipeline():
    reg = RegulationParser()
    audit = SystemAuditor()
    fix = FixSuggester()
    monitor = ComplianceMonitor(reg, audit, fix)

    company_data = {
        "company_name": "TestCo",
        "data_collected": ["email", "name"],
        "data_storage_location": "US",
        "ai_models_used": [],
        "user_count": 1000,
        "revenue": 100000,
        "processing_purposes": ["service"]
    }

    result = asyncio.run(monitor.analyze_compliance(company_data, ["GDPR", "CCPA"]))

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert isinstance(result["compliance_score"], float)
    assert "violations" in result
    assert "suggested_fixes" in result
