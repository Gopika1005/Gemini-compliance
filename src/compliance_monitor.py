import logging
from typing import Dict, List, Any
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ComplianceMonitor:
    def __init__(self, regulation_parser, system_auditor, fix_suggester):
        self.regulation_parser = regulation_parser
        self.system_auditor = system_auditor
        self.fix_suggester = fix_suggester
        
    async def analyze_compliance(self, company_data: Dict, regulations: List[str]) -> Dict:
        """Main compliance analysis pipeline"""
        try:
            logger.info(f"Starting compliance analysis for {company_data.get('company_name', 'Unknown')}")
            
            # Step 1: Parse regulations
            logger.info(f"Parsing {len(regulations)} regulations...")
            parsed_regulations = await self.regulation_parser.parse_regulations(regulations)
            
            # Step 2: Audit systems against regulations
            logger.info("Auditing company systems...")
            audit_results = await self.system_auditor.audit_systems(
                company_data, parsed_regulations
            )
            
            # Step 3: Calculate compliance score
            compliance_score = self._calculate_compliance_score(audit_results)
            
            # Step 4: Generate fix suggestions
            suggested_fixes = await self.fix_suggester.suggest_fixes(
                audit_results, company_data
            )
            
            # Step 5: Generate risk assessment
            risk_level, estimated_fine = self._assess_risk(
                audit_results, company_data.get("revenue", 0)
            )
            
            # Step 6: Generate audit report
            audit_report = self._generate_audit_report(
                company_data, audit_results, compliance_score, risk_level
            )
            
            return {
                "compliance_score": round(compliance_score, 2),
                "violations": audit_results.get("violations", []),
                "suggested_fixes": suggested_fixes,
                "audit_report": audit_report,
                "risk_level": risk_level,
                "estimated_fine": estimated_fine,
                "regulations": regulations,
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error in compliance analysis: {str(e)}")
            # Return error response
            return {
                "compliance_score": 0,
                "violations": [],
                "suggested_fixes": [],
                "audit_report": f"Analysis failed: {str(e)}",
                "risk_level": "unknown",
                "estimated_fine": None,
                "error": str(e)
            }
    
    def _calculate_compliance_score(self, audit_results: Dict) -> float:
        """Calculate overall compliance score (0-100)"""
        violations = audit_results.get("violations", [])
        total_checks = audit_results.get("total_checks", len(violations) + 10)  # Default
        
        if total_checks == 0:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {
            "critical": 5,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        weighted_score = 100.0
        for violation in violations:
            severity = violation.get("severity", "medium")
            weight = severity_weights.get(severity, 1)
            weighted_score -= (10 * weight) / total_checks
        
        return float(max(0.0, min(100.0, weighted_score)))
    
    def _assess_risk(self, audit_results: Dict, revenue: float) -> tuple:
        """Assess risk level and estimate potential fines"""
        violations = audit_results.get("violations", [])
        
        if not violations:
            return "low", 0.0
        
        # Calculate risk score
        risk_score = 0
        severity_points = {
            "critical": 10,
            "high": 6,
            "medium": 3,
            "low": 1
        }
        
        for violation in violations:
            severity = violation.get("severity", "medium")
            risk_score += severity_points.get(severity, 0)
        
        # Determine risk level
        if risk_score >= 20:
            risk_level = "critical"
            fine_percentage = 0.06  # 6% of revenue
        elif risk_score >= 10:
            risk_level = "high"
            fine_percentage = 0.04  # 4% of revenue
        elif risk_score >= 5:
            risk_level = "medium"
            fine_percentage = 0.02  # 2% of revenue
        else:
            risk_level = "low"
            fine_percentage = 0.01  # 1% of revenue
        
        estimated_fine = revenue * fine_percentage if revenue else None
        
        return risk_level, round(estimated_fine, 2) if estimated_fine else None
    
    def _generate_audit_report(self, company_data: Dict, audit_results: Dict, 
                              compliance_score: float, risk_level: str) -> str:
        """Generate human-readable audit report"""
        company_name = company_data.get("company_name", "Unknown Company")
        violations = audit_results.get("violations", [])
        
        report = f"""
COMPLIANCE AUDIT REPORT
======================

Company: {company_name}
Date: {datetime.now().strftime('%Y-%m-%d')}
Compliance Score: {compliance_score}/100
Risk Level: {risk_level.upper()}

SUMMARY
-------
Total Checks Performed: {audit_results.get('total_checks', 'N/A')}
Violations Found: {len(violations)}
Critical Issues: {sum(1 for v in violations if v.get('severity') == 'critical')}
High Priority Issues: {sum(1 for v in violations if v.get('severity') == 'high')}

DETAILED FINDINGS
-----------------
"""
        
        if violations:
            for i, violation in enumerate(violations, 1):
                report += f"""
{i}. {violation.get('regulation', 'Unknown')} - {violation.get('requirement', 'Requirement')}
    Severity: {violation.get('severity', 'medium').upper()}
    System Affected: {violation.get('system_affected', 'N/A')}
    Description: {violation.get('description', 'No description')}
    Evidence: {violation.get('evidence', 'No evidence provided')}
"""
        else:
            report += "✅ No violations found. Company is compliant with checked regulations.\n"
        
        report += f"""

RECOMMENDATIONS
---------------
{audit_results.get('summary', 'No specific recommendations provided.')}

NEXT STEPS
----------
1. Review all violations and suggested fixes
2. Prioritize fixes based on severity
3. Implement corrective actions
4. Schedule follow-up audit in 30 days
5. Document all compliance efforts

---
Generated by Gemini Compliance Monitor
AI-Powered Regulatory Compliance System
"""
        
        return report.strip()