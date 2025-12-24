import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/logs/compliance_monitor.log')
        ]
    )
    return logging.getLogger(__name__)

def save_json(data: Dict, filepath: str) -> None:
    """Save data as JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filepath: str) -> Dict:
    """Load data from JSON file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def format_currency(amount: float) -> str:
    """Format currency with commas"""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"

def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def validate_company_data(data: Dict) -> bool:
    """Validate company data structure"""
    required_fields = ["company_name", "data_collected", "ai_models_used", "user_count"]
    return all(field in data for field in required_fields)

def calculate_compliance_risk(score: float) -> str:
    """Calculate risk level from compliance score"""
    if score >= 90:
        return "low"
    elif score >= 70:
        return "medium"
    elif score >= 50:
        return "high"
    else:
        return "critical"

def generate_report_id(company_name: str) -> str:
    """Generate unique report ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company_name.lower().replace(" ", "_")[:20]
    return f"report_{safe_name}_{timestamp}"