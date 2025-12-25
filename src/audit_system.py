import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SystemAuditor:
    def __init__(self, model: Any = None):
        self.model = model

    async def audit_systems(self, company_data: Dict, regulations: Dict) -> Dict:
        """Audit company systems against regulations"""
        try:
            if self.model:
                # Use AI-powered audit
                return await self._audit_with_gemini(company_data, regulations)
            else:
                # Use rule-based audit
                return self._audit_with_rules(company_data, regulations)
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return self._get_default_audit_results()

    async def _audit_with_gemini(self, company_data: Dict, regulations: Dict) -> Dict:
        """Audit using Gemini AI"""
        try:
            prompt = self._create_audit_prompt(company_data, regulations)

            response = await self.model.generate_content_async(prompt)

            # Parse response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            audit_results = json.loads(text.strip())
            return self._validate_audit_results(audit_results)

        except Exception as e:
            logger.error(f"AI audit failed: {e}")
            return self._audit_with_rules(company_data, regulations)

    def _create_audit_prompt(self, company_data: Dict, regulations: Dict) -> str:
        """Create audit prompt for Gemini"""
        company_json = json.dumps(company_data, indent=2)
        regulations_json = json.dumps(regulations, indent=2)

        prompt = f"""
        You are a compliance auditor. Analyze this company's systems against regulations.
        
        COMPANY DATA:
        {company_json}
        
        REGULATIONS:
        {regulations_json}
        
        Analyze for compliance violations. Return ONLY valid JSON with this structure:
        {{
            "total_checks": 10,
            "passed_checks": 8,
            "violations": [
                {{
                    "id": "viol_1",
                    "regulation": "GDPR",
                    "requirement": "Requirement text",
                    "severity": "high",
                    "system_affected": "data_collection",
                    "description": "Detailed violation description",
                    "evidence": "Evidence from company data"
                }}
            ],
            "summary": "Overall audit summary",
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }}
        
        Focus on:
        1. Data collection and consent
        2. AI model transparency
        3. User rights implementation
        4. Data security measures
        5. Documentation and audit trails
        
        Be specific and reference the company data in evidence.
        """

        return prompt

    def _audit_with_rules(self, company_data: Dict, regulations: Dict) -> Dict:
        """Rule-based audit without AI"""
        violations = []
        company_name = company_data.get("company_name", "Unknown")

        # Check for common violations
        if "GDPR" in regulations:
            violations.extend(self._check_gdpr_compliance(company_data))

        if "CCPA" in regulations:
            violations.extend(self._check_ccpa_compliance(company_data))

        if "AI_ACT" in regulations:
            violations.extend(self._check_ai_act_compliance(company_data))

        return {
            "total_checks": len(violations) + 5,  # Estimate
            "passed_checks": max(0, 5 - len(violations)),
            "violations": violations,
            "summary": f"Found {len(violations)} violations in {company_name} systems.",
            "recommendations": [
                "Review data collection practices",
                "Implement consent management system",
                "Document AI model decision processes",
            ],
        }

    def _check_gdpr_compliance(self, company_data: Dict) -> List[Dict]:
        """Check GDPR compliance"""
        violations = []

        # Check data minimization
        data_collected = company_data.get("data_collected", [])
        if len(data_collected) > 10:  # Arbitrary threshold
            violations.append(
                {
                    "id": "gdpr_data_minimization",
                    "regulation": "GDPR",
                    "requirement": "Data minimization - collect only necessary data",
                    "severity": "medium",
                    "system_affected": "data_collection",
                    "description": "Company collects excessive personal data",
                    "evidence": f"Collects {len(data_collected)} data types",
                }
            )

        # Check international data transfer
        storage = company_data.get("data_storage_location", "").lower()
        if "global" in storage or "usa" in storage:
            violations.append(
                {
                    "id": "gdpr_international_transfer",
                    "regulation": "GDPR",
                    "requirement": "Adequate protection for international data transfers",
                    "severity": "high",
                    "system_affected": "data_storage",
                    "description": "EU data stored in non-adequate countries",
                    "evidence": f"Data stored in: {storage}",
                }
            )

        return violations

    def _check_ccpa_compliance(self, company_data: Dict) -> List[Dict]:
        """Check CCPA compliance"""
        violations = []

        # Check for California users
        user_count = company_data.get("user_count", 0)
        if user_count > 50000:
            violations.append(
                {
                    "id": "ccpa_threshold",
                    "regulation": "CCPA",
                    "requirement": "Compliance required for companies with 50k+ California consumers",
                    "severity": "high",
                    "system_affected": "general",
                    "description": "Company likely meets CCPA threshold",
                    "evidence": f"Has {user_count} users",
                }
            )

        return violations

    def _check_ai_act_compliance(self, company_data: Dict) -> List[Dict]:
        """Check AI Act compliance"""
        violations = []

        ai_models = company_data.get("ai_models_used", [])
        if ai_models:
            violations.append(
                {
                    "id": "aia_transparency",
                    "regulation": "AI_ACT",
                    "requirement": "Transparency for AI systems",
                    "severity": "medium",
                    "system_affected": "ai_models",
                    "description": "AI model documentation likely insufficient",
                    "evidence": f"Using {len(ai_models)} AI models",
                }
            )

        return violations

    def _validate_audit_results(self, audit_results: Dict) -> Dict:
        """Validate audit results structure"""
        if not isinstance(audit_results, dict):
            return self._get_default_audit_results()

        # Ensure required fields exist
        required = ["total_checks", "passed_checks", "violations", "summary"]
        for field in required:
            if field not in audit_results:
                audit_results[field] = [] if field == "violations" else ""

        # Ensure violations is a list
        if not isinstance(audit_results["violations"], list):
            audit_results["violations"] = []

        return audit_results

    def _get_default_audit_results(self) -> Dict:
        """Default audit results"""
        return {
            "total_checks": 0,
            "passed_checks": 0,
            "violations": [],
            "summary": "Audit could not be completed",
            "recommendations": ["Check system configuration and try again"],
        }
