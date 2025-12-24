import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FixSuggester:
    def __init__(self, model=None):
        self.model = model
        
    async def suggest_fixes(self, audit_results: Dict, company_data: Dict) -> List[Dict]:
        """Generate fix suggestions for violations"""
        try:
            violations = audit_results.get("violations", [])
            
            if not violations:
                return []
            
            if self.model:
                # Use AI for fix suggestions
                fixes = await self._suggest_fixes_with_gemini(violations, company_data)
            else:
                # Use template-based fixes
                fixes = self._suggest_fixes_with_templates(violations, company_data)
            
            # Prioritize and sort fixes
            return self._prioritize_fixes(fixes)
            
        except Exception as e:
            logger.error(f"Error generating fixes: {e}")
            return []
    
    async def _suggest_fixes_with_gemini(self, violations: List[Dict], company_data: Dict) -> List[Dict]:
        """Generate fixes using Gemini AI"""
        try:
            prompt = self._create_fix_prompt(violations, company_data)
            response = await self.model.generate_content_async(prompt)
            
            # Parse response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            fixes = json.loads(text.strip())
            
            if isinstance(fixes, dict) and "fixes" in fixes:
                return fixes["fixes"]
            elif isinstance(fixes, list):
                return fixes
            else:
                return self._suggest_fixes_with_templates(violations, company_data)
                
        except Exception as e:
            logger.error(f"AI fix generation failed: {e}")
            return self._suggest_fixes_with_templates(violations, company_data)
    
    def _create_fix_prompt(self, violations: List[Dict], company_data: Dict) -> str:
        """Create prompt for fix generation"""
        violations_json = json.dumps(violations, indent=2)
        company_info = json.dumps({
            "industry": company_data.get("industry", "Technology"),
            "size": company_data.get("user_count", 0),
            "tech_stack": company_data.get("ai_models_used", [])
        }, indent=2)
        
        prompt = f"""
        Generate actionable fix suggestions for these compliance violations.
        
        VIOLATIONS:
        {violations_json}
        
        COMPANY CONTEXT:
        {company_info}
        
        For each violation, provide a practical fix. Return ONLY valid JSON array:
        [
            {{
                "violation_id": "matching_id",
                "title": "Fix Title",
                "description": "Detailed description",
                "steps": ["Step 1", "Step 2"],
                "estimated_time_hours": 24,
                "required_resources": ["developer", "legal"],
                "priority": "critical|high|medium|low",
                "cost_estimate_usd": 5000,
                "compliance_impact": "Will resolve violation"
            }}
        ]
        
        Make fixes specific, actionable, and appropriate for the company size.
        """
        
        return prompt
    
    def _suggest_fixes_with_templates(self, violations: List[Dict], company_data: Dict) -> List[Dict]:
        """Generate fixes using templates"""
        fixes = []
        company_size = company_data.get("user_count", 0)
        
        # Map violation types to fix templates
        fix_templates = {
            "data_minimization": {
                "title": "Implement Data Minimization Policy",
                "description": "Reduce collected data to only what's necessary",
                "steps": [
                    "Audit current data collection",
                    "Identify unnecessary data fields",
                    "Update data collection forms",
                    "Delete historical unnecessary data"
                ],
                "estimated_time_hours": 40,
                "required_resources": ["data_engineer", "legal"],
                "priority": "medium",
                "cost_estimate_usd": 8000,
                "compliance_impact": "Resolves data minimization requirements"
            },
            "user_consent": {
                "title": "Deploy Consent Management Platform",
                "description": "Implement proper user consent collection and management",
                "steps": [
                    "Select consent management tool",
                    "Design consent collection UI",
                    "Integrate with data systems",
                    "Test and deploy"
                ],
                "estimated_time_hours": 60,
                "required_resources": ["frontend_dev", "backend_dev", "legal"],
                "priority": "high",
                "cost_estimate_usd": 15000,
                "compliance_impact": "Ensures proper consent collection"
            },
            "ai_transparency": {
                "title": "Create AI Model Documentation",
                "description": "Document AI models for transparency requirements",
                "steps": [
                    "Document model purpose and capabilities",
                    "Describe training data and methodology",
                    "Outline decision-making process",
                    "Create user-facing explanations"
                ],
                "estimated_time_hours": 30,
                "required_resources": ["data_scientist", "technical_writer"],
                "priority": "medium",
                "cost_estimate_usd": 6000,
                "compliance_impact": "Meets AI transparency requirements"
            }
        }
        
        # Apply templates based on violation types
        for violation in violations[:5]:  # Limit to 5 fixes
            regulation = violation.get("regulation", "").lower()
            requirement = violation.get("requirement", "").lower()
            
            # Determine which template to use
            template_key = "user_consent"  # Default
            
            if "data" in requirement or "collection" in requirement:
                template_key = "data_minimization"
            elif "ai" in requirement or "model" in requirement:
                template_key = "ai_transparency"
            elif "consent" in requirement or "opt-out" in requirement:
                template_key = "user_consent"
            
            template = fix_templates.get(template_key, fix_templates["user_consent"])
            
            # Customize based on company size
            cost_multiplier = 1.0
            time_multiplier = 1.0
            if company_size > 100000:
                cost_multiplier = 2.0
                time_multiplier = 1.5
            elif company_size < 1000:
                cost_multiplier = 0.5
                time_multiplier = 0.8
            
            fixes.append({
                "violation_id": violation.get("id", "unknown"),
                "title": template["title"],
                "description": template["description"],
                "steps": template["steps"],
                "estimated_time_hours": int(template["estimated_time_hours"] * time_multiplier),
                "required_resources": template["required_resources"],
                "priority": violation.get("severity", "medium"),
                "cost_estimate_usd": int(template["cost_estimate_usd"] * cost_multiplier),
                "compliance_impact": template["compliance_impact"]
            })
        
        return fixes
    
    def _prioritize_fixes(self, fixes: List[Dict]) -> List[Dict]:
        """Prioritize fixes by severity and impact"""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        def get_priority(fix):
            return priority_order.get(fix.get("priority", "low"), 3)
        
        return sorted(fixes, key=get_priority)