import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from contextlib import asynccontextmanager

    import google.generativeai as genai  # type: ignore
    from dotenv import load_dotenv
    from fastapi import BackgroundTasks, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    from src.audit_system import SystemAuditor
    from src.compliance_monitor import ComplianceMonitor
    from src.fix_suggester import FixSuggester
    from src.regulation_parser import RegulationParser
    from src.utils import setup_logging
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables
load_dotenv()

from config.settings import settings

# Setup logging
logger = setup_logging()


# Lifespan handler (replaces deprecated @app.on_event startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize system components on startup and teardown on shutdown"""
    logger.info("🚀 Starting Gemini Compliance Monitor...")

    # Check API key using centralized settings
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("⚠️  Gemini API key not configured. Using mock mode.")
        app.state.mock_mode = True  # type: ignore
    else:
        app.state.mock_mode = False  # type: ignore
        genai.configure(api_key=api_key)

    # Store general API key in app state for other components
    app.state.api_key = settings.API_KEY  # type: ignore

    app.state.system = await initialize_system()  # type: ignore
    try:
        yield
    finally:
        # Place for graceful shutdown if needed
        pass


# Initialize FastAPI app
app = FastAPI(
    title="Gemini Compliance Monitor API",
    description="AI-Powered Real-time Regulatory Compliance System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class CompanyData(BaseModel):
    company_name: str
    data_collected: List[str]
    data_storage_location: str = "global"
    ai_models_used: List[str]
    user_count: int
    revenue: Optional[float] = None
    processing_purposes: List[str] = ["Analytics"]
    industry: Optional[str] = "Technology"


class ComplianceRequest(BaseModel):
    company_data: CompanyData
    regulations: List[str]
    priority: str = "medium"
    generate_report: bool = True


class ComplianceResponse(BaseModel):
    status: str
    compliance_score: float
    violations: List[Dict]
    suggested_fixes: List[Dict]
    audit_report: str
    risk_level: str
    estimated_fine: Optional[float]
    report_url: Optional[str]
    timestamp: str


# Startup handled via lifespan handler defined above


async def initialize_system():
    """Initialize the compliance system"""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel("gemini-pro") if not app.state.mock_mode else None  # type: ignore

        # Initialize components
        regulation_parser = RegulationParser(model)
        system_auditor = SystemAuditor(model)
        fix_suggester = FixSuggester(model)
        monitor = ComplianceMonitor(regulation_parser, system_auditor, fix_suggester)

        logger.info("✅ System initialized successfully")
        return monitor
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        return None


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "message": "Gemini Compliance Monitoring System",
        "version": "2.0.0",
        "status": "operational",
        "regulations_supported": ["GDPR", "CCPA", "DMA", "AI_ACT", "HIPAA", "PIPEDA"],
        "features": [
            "Real-time compliance monitoring",
            "AI-powered regulation parsing",
            "Automated fix suggestions",
            "Risk assessment and fine estimation",
            "Detailed audit reports",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "compliance-monitor",
    }


@app.post("/analyze-compliance", response_model=ComplianceResponse)
async def analyze_compliance(
    request: ComplianceRequest, background_tasks: BackgroundTasks
):
    """
    Analyze compliance for given company data and regulations

    - **company_data**: Company information and systems
    - **regulations**: List of regulations to check
    - **priority**: Analysis priority (low/medium/high)
    - **generate_report**: Whether to generate PDF report
    """
    try:
        if not app.state.system:  # type: ignore
            raise HTTPException(status_code=503, detail="System not initialized")

        company_dict = request.company_data.model_dump()

        # Run compliance analysis
        result = await app.state.system.analyze_compliance(  # type: ignore
            company_dict, request.regulations
        )

        # Add report URL if requested
        if request.generate_report:
            report_url = f"/reports/{company_dict['company_name'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            result["report_url"] = report_url

        result["status"] = "completed"
        result["timestamp"] = datetime.now().isoformat()

        # Store audit in background
        background_tasks.add_task(store_audit_log, company_dict, result)

        return ComplianceResponse(**result)

    except Exception as e:
        logger.error(f"Error analyzing compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/regulations")
async def get_regulations():
    """Get list of supported regulations with details"""
    regulations = {
        "GDPR": {
            "name": "General Data Protection Regulation",
            "region": "European Union",
            "enforced_since": "2018",
            "max_fine": "4% of global revenue or €20M",
            "key_requirements": [
                "Data minimization",
                "Purpose limitation",
                "Right to erasure",
                "Data protection by design",
            ],
        },
        "CCPA": {
            "name": "California Consumer Privacy Act",
            "region": "California, USA",
            "enforced_since": "2020",
            "max_fine": "$7,500 per intentional violation",
            "key_requirements": [
                "Right to know",
                "Right to delete",
                "Right to opt-out",
                "Non-discrimination",
            ],
        },
        "AI_ACT": {
            "name": "EU Artificial Intelligence Act",
            "region": "European Union",
            "status": "Upcoming",
            "max_fine": "6% of global revenue",
            "key_requirements": [
                "Risk-based classification",
                "Prohibited AI practices",
                "High-risk AI requirements",
                "Transparency obligations",
            ],
        },
    }
    return {"regulations": regulations}


@app.post("/quick-check")
async def quick_compliance_check(company_name: str, industry: str = "Technology"):
    """
    Quick compliance check for common regulations
    """
    sample_data = {
        "company_name": company_name,
        "data_collected": ["email", "name", "location"],
        "data_storage_location": "global",
        "ai_models_used": ["basic_analytics"],
        "user_count": 1000,
        "revenue": 1000000,
        "processing_purposes": ["service_delivery"],
        "industry": industry,
    }

    request = ComplianceRequest(
        company_data=CompanyData(**sample_data),  # type: ignore
        regulations=["GDPR", "CCPA"],
        priority="low",
    )

    return await analyze_compliance(request, BackgroundTasks())


async def store_audit_log(company_data: Dict, result: Dict):
    """Store audit logs asynchronously"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "company": company_data.get("company_name"),
            "compliance_score": result.get("compliance_score"),
            "risk_level": result.get("risk_level"),
            "violations_count": len(result.get("violations", [])),
            "regulations_checked": result.get("regulations", []),
        }
        logger.info(f"Audit stored: {log_entry}")
    except Exception as e:
        logger.error(f"Failed to store audit log: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        log_level="info",
    )
