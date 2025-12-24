import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RegulationParser:
    def __init__(self, model=None):
        self.model = model
        self.regulation_cache = {}

    async def parse_regulation_from_text(
        self, regulation_text: str, regulation_name: str
    ) -> Dict:
        """Parse regulation text"""
        try:
            if self.model:
                # Use Gemini AI for parsing
                return await self._parse_with_gemini(regulation_text, regulation_name)
            else:
                # Use fallback parsing
                return self._parse_with_fallback(regulation_name)
        except Exception as e:
            logger.error(f"Error parsing regulation: {str(e)}")
            return self._get_default_regulation(regulation_name)

    async def _parse_with_gemini(
        self, regulation_text: str, regulation_name: str
    ) -> Dict:
        """Parse regulation using Gemini AI"""
        try:
            prompt = f"""
            Analyze this {regulation_name} regulation and extract key compliance requirements.
            Return ONLY valid JSON with this exact structure:
            {{
                "regulation_name": "{regulation_name}",
                "key_requirements": [
                    {{
                        "id": "req_1",
                        "requirement": "specific requirement text",
                        "category": "data_protection|user_consent|transparency|security|audit",
                        "severity": "critical|high|medium|low"
                    }}
                ],
                "applicable_systems": ["data_collection", "data_storage", "ai_models", "user_interface"],
                "penalties": {{
                    "max_fine_percentage": 0.06,
                    "description": "fine description"
                }}
            }}
            
            Regulation: {regulation_text[:1000]}...
            """

            response = await self.model.generate_content_async(prompt)

            # Clean response text
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())

        except Exception as e:
            logger.error(f"Gemini parsing failed: {e}")
            return self._parse_with_fallback(regulation_name)

    def _parse_with_fallback(self, regulation_name: str) -> Dict:
        """Fallback parsing without AI"""
        regulations = {
            "GDPR": {
                "regulation_name": "GDPR",
                "key_requirements": [
                    {
                        "id": "gdpr_1",
                        "requirement": "Obtain explicit consent for data processing",
                        "category": "user_consent",
                        "severity": "high",
                    },
                    {
                        "id": "gdpr_2",
                        "requirement": "Implement data protection by design and by default",
                        "category": "security",
                        "severity": "high",
                    },
                    {
                        "id": "gdpr_3",
                        "requirement": "Notify authorities of data breaches within 72 hours",
                        "category": "transparency",
                        "severity": "critical",
                    },
                ],
                "applicable_systems": [
                    "data_collection",
                    "data_storage",
                    "user_interface",
                ],
                "penalties": {
                    "max_fine_percentage": 0.04,
                    "description": "Up to 4% of global annual turnover",
                },
            },
            "CCPA": {
                "regulation_name": "CCPA",
                "key_requirements": [
                    {
                        "id": "ccpa_1",
                        "requirement": "Provide right to opt-out of data sale",
                        "category": "user_consent",
                        "severity": "high",
                    },
                    {
                        "id": "ccpa_2",
                        "requirement": "Disclose data collection practices",
                        "category": "transparency",
                        "severity": "medium",
                    },
                    {
                        "id": "ccpa_3",
                        "requirement": "Honor deletion requests within 45 days",
                        "category": "data_protection",
                        "severity": "high",
                    },
                ],
                "applicable_systems": ["data_collection", "user_interface"],
                "penalties": {
                    "max_fine_percentage": 0.025,
                    "description": "$2,500-$7,500 per violation",
                },
            },
            "AI_ACT": {
                "regulation_name": "AI_ACT",
                "key_requirements": [
                    {
                        "id": "aia_1",
                        "requirement": "Conduct risk assessment for high-risk AI systems",
                        "category": "audit",
                        "severity": "critical",
                    },
                    {
                        "id": "aia_2",
                        "requirement": "Ensure human oversight of AI decisions",
                        "category": "transparency",
                        "severity": "high",
                    },
                    {
                        "id": "aia_3",
                        "requirement": "Maintain documentation of AI system development",
                        "category": "audit",
                        "severity": "medium",
                    },
                ],
                "applicable_systems": ["ai_models", "data_collection"],
                "penalties": {
                    "max_fine_percentage": 0.06,
                    "description": "Up to 6% of global annual turnover",
                },
            },
        }

        return regulations.get(
            regulation_name, self._get_default_regulation(regulation_name)
        )

    async def parse_regulations(self, regulation_names: List[str]) -> Dict:
        """Parse multiple regulations"""
        regulations = {}

        for reg_name in regulation_names:
            if reg_name in self.regulation_cache:
                regulations[reg_name] = self.regulation_cache[reg_name]
                continue

            # Try to load from file first
            file_path = f"data/regulations/{reg_name.lower()}.json"
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        regulations[reg_name] = json.load(f)
                    self.regulation_cache[reg_name] = regulations[reg_name]
                    continue
                except Exception as e:
                    logger.warning(f"Could not load regulation from file: {e}")

            # Parse regulation
            regulation_text = self._get_regulation_text(reg_name)
            parsed = await self.parse_regulation_from_text(regulation_text, reg_name)

            self.regulation_cache[reg_name] = parsed
            regulations[reg_name] = parsed

        return regulations

    def _get_regulation_text(self, regulation_name: str) -> str:
        """Get regulation text"""
        regulation_texts = {
            "GDPR": "General Data Protection Regulation (GDPR) is a privacy law in the EU...",
            "CCPA": "California Consumer Privacy Act (CCPA) gives consumers rights over their personal information...",
            "AI_ACT": "EU Artificial Intelligence Act regulates AI systems based on risk levels...",
        }
        return regulation_texts.get(regulation_name, f"Regulation: {regulation_name}")

    def _get_default_regulation(self, regulation_name: str) -> Dict:
        """Return default regulation structure"""
        return {
            "regulation_name": regulation_name,
            "key_requirements": [],
            "applicable_systems": [],
            "penalties": {"max_fine_percentage": 0.04, "description": "Standard fine"},
        }
