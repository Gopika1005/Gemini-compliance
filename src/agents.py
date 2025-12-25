"""
ReguBrain Multi-Agent System: Advanced AI Agents for Compliance
"""

import json
from typing import Any, Dict, List, Optional

import google.generativeai as genai


class ComplianceAgent:
    def __init__(self, name: str, role: str, goal: str, model: Any):
        self.name = name
        self.role = role
        self.goal = goal
        self.model = model

    async def run(self, context: str, task: str) -> str:
        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        
        Context: {context}
        
        Task: {task}
        
        Provide a detailed response focused on your role.
        """
        response = await self.model.generate_content_async(prompt)
        return response.text


class MultiAgentSystem:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

        self.researcher = ComplianceAgent(
            "Researcher",
            "Technical Compliance Researcher",
            "Extract critical requirements from complex legal and technical documents.",
            self.model,
        )

        self.auditor = ComplianceAgent(
            "Auditor",
            "System Integrity Auditor",
            "Detect gaps between company data and regulatory requirements.",
            self.model,
        )

        self.advisor = ComplianceAgent(
            "Advisor",
            "Strategic Compliance Advisor",
            "Generate actionable remediation plans and business risk summaries.",
            self.model,
        )

    async def get_consultation(self, query: str, history: List[Dict] = []) -> str:
        """Chat consultant logic"""
        chat = self.model.start_chat(history=history or [])
        response = await chat.send_message_async(query)
        return response.text

    async def process_document(self, text: str) -> Dict:
        """Process a raw regulation document into a structured summary"""
        task = "Analyze this document and extract the top 5 mandatory compliance requirements as a JSON object."
        result = await self.researcher.run(text, task)
        try:
            # Attempt to find JSON in the response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(result[start:end])
            return {"error": "Could not structure data", "raw": result[:500]}
        except:
            return {"error": "Parsing error", "raw": result[:500]}
