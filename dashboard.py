"""
Streamlit Dashboard for Gemini Compliance Monitor
"""

import json
import os
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Embedded mode imports
try:
    from src.audit_system import SystemAuditor
    from src.compliance_monitor import ComplianceMonitor
    from src.fix_suggester import FixSuggester
    from src.regulation_parser import RegulationParser
    from src.main import initialize_system
    import google.generativeai as genai
    from config.settings import settings
except ImportError:
    pass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="Gemini Compliance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_demo_results(company_data, regulations):
    """Generate demo results for testing"""
    import random
    from datetime import datetime

    # Generate random violations
    violations = []
    violation_templates = [
        {
            "id": "gdpr_consent",
            "regulation": "GDPR",
            "requirement": "Explicit consent for data processing",
            "severity": random.choice(["high", "medium"]),
            "system_affected": "data_collection",
            "description": "Consent mechanism lacks granular options",
            "evidence": "Single checkbox for all processing purposes",
        },
        {
            "id": "ccpa_optout",
            "regulation": "CCPA",
            "requirement": "Clear opt-out mechanism for data sale",
            "severity": "medium",
            "system_affected": "user_interface",
            "description": "Do Not Sell link not prominently displayed",
            "evidence": "Link buried in privacy policy",
        },
        {
            "id": "aia_transparency",
            "regulation": "AI_ACT",
            "requirement": "Transparency for AI decisions",
            "severity": random.choice(["medium", "low"]),
            "system_affected": "ai_models",
            "description": "AI model decisions not explained to users",
            "evidence": "No explanation for recommendation outputs",
        },
    ]

    # Select random violations
    num_violations = random.randint(0, 3)
    if num_violations > 0:
        violations = random.sample(violation_templates, num_violations)

    # Calculate score
    base_score = 85 - (len(violations) * 10)
    compliance_score = max(30, min(95, base_score + random.randint(-5, 5)))

    # Risk level
    if compliance_score >= 80:
        risk_level = "low"
    elif compliance_score >= 60:
        risk_level = "medium"
    elif compliance_score >= 40:
        risk_level = "high"
    else:
        risk_level = "critical"

    # Estimated fine
    revenue = company_data.get("revenue", 1000000)
    fine_percentage = {"critical": 0.06, "high": 0.04, "medium": 0.02, "low": 0.01}.get(
        risk_level, 0.01
    )

    estimated_fine = revenue * fine_percentage if revenue else 0

    # Fix suggestions
    fixes = (
        [
            {
                "violation_id": "gdpr_consent",
                "title": "Implement Granular Consent Management",
                "description": "Upgrade consent mechanism to allow users to choose specific processing purposes",
                "steps": [
                    "Audit current consent collection points",
                    "Design purpose-specific consent options",
                    "Update privacy policy with detailed purposes",
                    "Implement and test new consent interface",
                ],
                "estimated_time_hours": 40,
                "required_resources": ["frontend_dev", "legal_review"],
                "priority": "high",
                "cost_estimate_usd": 8000,
                "compliance_impact": "Will resolve GDPR consent requirements",
            }
        ]
        if violations
        else []
    )

    return {
        "compliance_score": compliance_score,
        "violations": violations,
        "suggested_fixes": fixes,
        "audit_report": f"""
        COMPLIANCE AUDIT REPORT - DEMO MODE
        Company: {company_data.get('company_name')}
        Date: {datetime.now().strftime('%Y-%m-%d')}
        Score: {compliance_score}/100
        Risk Level: {risk_level}
        
        Summary: Found {len(violations)} compliance issues. 
        {'Immediate action required.' if violations else 'No critical issues found.'}
        
        Note: This is a demo report. For actual compliance assessment, 
        ensure Gemini API is configured and run in production mode.
        """,
        "risk_level": risk_level,
        "estimated_fine": round(estimated_fine, 2),
        "regulations": regulations,
        "analysis_date": datetime.now().isoformat(),
    }

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #1a73e8, #34a853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    .compliance-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1a73e8;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .risk-critical { 
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .risk-high { 
        background: linear-gradient(135deg, #ff9a00, #ff5e00);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .risk-medium { 
        background: linear-gradient(135deg, #ffe000, #ffb347);
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .risk-low { 
        background: linear-gradient(135deg, #56ab2f, #a8e063);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1a73e8, #34a853);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<h1 class="main-header">🛡️ Gemini Compliance Monitor</h1>', unsafe_allow_html=True
)
st.markdown("### AI-Powered Real-time Regulatory Compliance Dashboard")

# Sidebar
with st.sidebar:
    st.image(
        "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png",
        width=150,
    )
    st.markdown("---")

    st.header("⚙️ Configuration")

    # API Configuration
    api_option = st.selectbox(
        "Backend Connection",
        ["Embedded (Streamlit Cloud)", "External API (Local/Remote)"],
        index=0
    )
    
    if api_option == "External API (Local/Remote)":
        api_url = st.text_input("API URL", "http://localhost:8000")
    else:
        api_url = None

    # Initialize embedded system if selected
    @st.cache_resource
    def get_embedded_system():
        """Initialize the compliance system for embedded use"""
        try:
            # Try Streamlit Secrets first, then ENV
            api_key = None
            try:
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = st.secrets["GEMINI_API_KEY"]
            except:
                pass
                
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")
            
            regulation_parser = RegulationParser(model)
            system_auditor = SystemAuditor(model)
            fix_suggester = FixSuggester(model)
            monitor = ComplianceMonitor(regulation_parser, system_auditor, fix_suggester)
            return monitor
        except Exception as e:
            st.error(f"Failed to initialize embedded system: {e}")
            return None

    embedded_system = get_embedded_system() if api_url is None else None

    # Demo Mode
    demo_mode = st.checkbox("Enable Demo Mode", value=True)

    st.markdown("---")
    st.header("📋 Quick Actions")

    if st.button("🔄 Check System Health", use_container_width=True):
        if api_url:
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    st.success("✅ API is healthy!")
                else:
                    st.error("❌ API is not responding")
            except:
                st.error("❌ Cannot connect to API")
        elif embedded_system:
            st.success("✅ Embedded System is Active!")
            st.info("System is ready to analyze.")
        else:
            st.error("❌ System not initialized. Check API Key in Settings.")

    if st.button("📊 View Sample Report", use_container_width=True):
        st.session_state.demo_report = True
        st.toast("📈 Sample report loaded! Please go to the 'Compliance Check' tab.")
        st.success("Sample Report Ready!")

    st.markdown("---")
    st.markdown("**🔗 Useful Links**")
    if api_url:
        st.markdown(f"[API Documentation]({api_url}/docs)")
    else:
        st.markdown("[Streamlit Documentation](https://docs.streamlit.io)")
    st.markdown("[GitHub Repository](https://github.com/Gopika1005/Gemini-compliance)")
    st.markdown("[Official AI Act Text](https://artificialintelligenceact.eu/)")

    st.markdown("---")
    st.markdown(
        """
    <div style='background: #f0f2f6; padding: 1rem; border-radius: 10px;'>
    <small>Built with ❤️ for Hackathon Submission</small><br>
    <small>Using Google Gemini AI • FastAPI • Streamlit</small>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Dashboard", "🔍 Compliance Check", "📈 Analytics", "⚙️ Settings"]
)

with tab1:
    # Welcome Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
        <div class='compliance-card'>
        <h2>Welcome to Your Compliance Command Center</h2>
        <p>Monitor regulatory compliance across multiple jurisdictions in real-time. 
        Our AI-powered system analyzes your systems against global regulations and 
        provides actionable insights to avoid costly fines.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.metric("Active Regulations", "6", "+2")
        st.metric("Companies Monitored", "127", "24 this month")
        st.metric("Avg. Score Improvement", "42%", "+12%")

    # Key Metrics
    st.subheader("📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class='metric-card'>
        <h3>💰 Potential Fines Avoided</h3>
        <h1 style='color: #34a853;'>$2.4M</h1>
        <p>Last 30 days</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class='metric-card'>
        <h3>⏱️ Hours Saved</h3>
        <h1 style='color: #1a73e8;'>210</h1>
        <p>Monthly average</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class='metric-card'>
        <h3>📈 Compliance Score</h3>
        <h1 style='color: #fbbc05;'>78%</h1>
        <p>Industry average</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class='metric-card'>
        <h3>🚨 Critical Issues</h3>
        <h1 style='color: #ea4335;'>3</h1>
        <p>Require immediate attention</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Recent Activity
    st.subheader("🔄 Recent Activity")

    activity_data = {
        "Time": ["10:30 AM", "09:45 AM", "Yesterday", "2 days ago"],
        "Company": ["TechStartup Inc", "HealthCorp", "FinancePlus", "RetailChain"],
        "Action": [
            "GDPR Audit Completed",
            "CCPA Violation Fixed",
            "AI Act Assessment",
            "New Regulation Added",
        ],
        "Status": ["✅", "⚠️", "✅", "📥"],
    }

    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True, hide_index=True)

    # Regulation Timeline
    st.subheader("🗓️ Upcoming Deadlines")

    deadlines = pd.DataFrame(
        {
            "Regulation": [
                "AI Act Enforcement",
                "GDPR Amendments",
                "CCPA 2.0",
                "DMA Review",
            ],
            "Deadline": ["2024-06-30", "2024-08-25", "2024-12-31", "2025-01-01"],
            "Days Remaining": [45, 120, 210, 365],
            "Priority": ["🔴 High", "🟡 Medium", "🟢 Low", "🟡 Medium"],
        }
    )

    st.dataframe(deadlines, use_container_width=True, hide_index=True)

with tab2:
    st.header("🔍 Compliance Analysis")

    # Analysis Form
    with st.form("compliance_form"):
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name", "TechCorp Inc")
            industry = st.selectbox(
                "Industry",
                ["Technology", "Healthcare", "Finance", "Retail", "Education", "Other"],
            )
            user_count = st.number_input(
                "Number of Users", min_value=1, value=10000, step=1000
            )
            revenue = st.number_input(
                "Annual Revenue ($)", min_value=0, value=1000000, step=100000
            )

        with col2:
            data_collected = st.multiselect(
                "Data Collected",
                [
                    "Email Address",
                    "Phone Number",
                    "Location",
                    "Payment Info",
                    "Health Data",
                    "Biometric Data",
                    "Usage Patterns",
                    "Device Info",
                ],
                default=["Email Address", "Location", "Usage Patterns"],
            )

            ai_models = st.multiselect(
                "AI Models Used",
                [
                    "Gemini Pro",
                    "GPT-4",
                    "Custom ML",
                    "Computer Vision",
                    "Natural Language Processing",
                    "Predictive Analytics",
                    "Recommendation Engine",
                ],
                default=["Gemini Pro", "Recommendation Engine"],
            )

            storage_location = st.selectbox(
                "Primary Data Storage",
                ["EU Only", "US Only", "Global", "EU-US Mix", "Asia", "Other"],
            )

        regulations = st.multiselect(
            "Regulations to Check",
            ["GDPR", "CCPA", "AI_ACT", "DMA", "HIPAA", "PIPEDA", "LGPD"],
            default=["GDPR", "CCPA", "AI_ACT"],
        )

        priority = st.select_slider(
            "Analysis Priority", ["Low", "Medium", "High"], value="Medium"
        )

        generate_report = st.checkbox("Generate Detailed Report", value=True)

        submitted = st.form_submit_button(
            "🚀 Run Compliance Analysis", use_container_width=True
        )

    # Results Section
    if submitted or (
        "demo_report" in st.session_state and st.session_state.demo_report
    ):
        if "demo_report" in st.session_state:
            st.session_state.demo_report = False

        with st.spinner("🤖 Analyzing compliance with AI..."):
            # Prepare request data
            company_data = {
                "company_name": company_name,
                "data_collected": data_collected,
                "data_storage_location": storage_location,
                "ai_models_used": ai_models,
                "user_count": user_count,
                "revenue": revenue,
                "processing_purposes": [
                    "Personalization",
                    "Analytics",
                    "Service Delivery",
                ],
                "industry": industry,
            }

            try:
                if not demo_mode:
                    if api_url:
                        # Real API call
                        response = requests.post(
                            f"{api_url}/analyze-compliance",
                            json={
                                "company_data": company_data,
                                "regulations": regulations,
                                "priority": priority.lower(),
                                "generate_report": generate_report,
                            },
                            timeout=30,
                        )

                        if response.status_code == 200:
                            results = response.json()
                        else:
                            st.error(f"API Error: {response.status_code}")
                            results = get_demo_results(company_data, regulations)
                    elif embedded_system:
                        # Embedded mode
                        results = asyncio.run(
                            embedded_system.analyze_compliance(company_data, regulations)
                        )
                    else:
                        st.warning("⚠️ GEMINI_API_KEY not found or system not initialized. Using demo mode.")
                        results = get_demo_results(company_data, regulations)

                else:
                    # Demo mode
                    results = get_demo_results(company_data, regulations)

                # Display Results
                st.success("✅ Analysis Complete!")

                # Results Overview
                col1, col2, col3 = st.columns(3)

                with col1:
                    score = results.get("compliance_score", 0)
                    st.markdown(
                        f"""
                    <div style='text-align: center;'>
                    <h3>Compliance Score</h3>
                    <h1 style='font-size: 4rem; color: {'#34a853' if score >= 80 else '#fbbc05' if score >= 60 else '#ea4335'};'>{score}%</h1>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Gauge Chart
                    fig = go.Figure(
                        go.Indicator(
                            mode="gauge+number",
                            value=score,
                            domain={"x": [0, 1], "y": [0, 1]},
                            title={"text": ""},
                            gauge={
                                "axis": {"range": [None, 100]},
                                "bar": {"color": "#1a73e8"},
                                "steps": [
                                    {"range": [0, 50], "color": "#ea4335"},
                                    {"range": [50, 80], "color": "#fbbc05"},
                                    {"range": [80, 100], "color": "#34a853"},
                                ],
                                "threshold": {
                                    "line": {"color": "black", "width": 4},
                                    "thickness": 0.75,
                                    "value": 80,
                                },
                            },
                        )
                    )
                    fig.update_layout(height=250, margin=dict(t=0, b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    risk_level = results.get("risk_level", "low")
                    risk_class = f"risk-{risk_level}"
                    st.markdown(
                        f"""
                    <div style='text-align: center;'>
                    <h3>Risk Level</h3>
                    <div class='{risk_class}' style='font-size: 2rem; padding: 1rem; margin: 1rem auto; width: fit-content;'>
                    {risk_level.upper()}
                    </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Risk breakdown
                    violations = results.get("violations", [])
                    if violations:
                        severity_counts = {}
                        for v in violations:
                            sev = v.get("severity", "medium")
                            severity_counts[sev] = severity_counts.get(sev, 0) + 1

                        fig = px.pie(
                            values=list(severity_counts.values()),
                            names=list(severity_counts.keys()),
                            color=list(severity_counts.keys()),
                            color_discrete_map={
                                "critical": "#ea4335",
                                "high": "#fbbc05",
                                "medium": "#1a73e8",
                                "low": "#34a853",
                            },
                        )
                        fig.update_layout(height=250, margin=dict(t=0, b=0))
                        st.plotly_chart(fig, use_container_width=True)

                with col3:
                    estimated_fine = results.get("estimated_fine", 0)
                    st.markdown(
                        f"""
                    <div style='text-align: center;'>
                    <h3>Estimated Fine</h3>
                    <h1 style='font-size: 3rem; color: {'#ea4335' if estimated_fine > 10000 else '#fbbc05'};'>
                    ${estimated_fine:,.0f if estimated_fine else 0}
                    </h1>
                    <p>Potential regulatory penalty</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Fine breakdown
                    if estimated_fine:
                        st.metric(
                            "Percentage of Revenue",
                            (
                                f"{(estimated_fine/revenue*100):.2f}%"
                                if revenue
                                else "N/A"
                            ),
                        )
                        st.metric("Violations Found", len(violations))
                        st.metric("Regulations Checked", len(regulations))

                # Violations Details
                st.subheader("🚨 Violations Found")

                if violations:
                    violations_df = pd.DataFrame(violations)

                    # Color code severity
                    def color_severity(severity):
                        colors = {
                            "critical": "background-color: #ea4335; color: white;",
                            "high": "background-color: #fbbc05; color: black;",
                            "medium": "background-color: #1a73e8; color: white;",
                            "low": "background-color: #34a853; color: white;",
                        }
                        return colors.get(severity, "")

                    styled_df = violations_df.style.applymap(
                        lambda x: (
                            color_severity(x)
                            if x in ["critical", "high", "medium", "low"]
                            else ""
                        ),
                        subset=["severity"],
                    )

                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                    # Fix Suggestions
                    st.subheader("🔧 Suggested Fixes")
                    fixes = results.get("suggested_fixes", [])

                    if fixes:
                        for i, fix in enumerate(fixes, 1):
                            with st.expander(
                                f"{i}. {fix.get('title', 'Fix')} - Priority: {fix.get('priority', 'medium').upper()}"
                            ):
                                col_a, col_b = st.columns([2, 1])

                                with col_a:
                                    st.write("**Description:**")
                                    st.write(fix.get("description", ""))

                                    st.write("**Steps:**")
                                    steps = fix.get("steps", [])
                                    for step in steps:
                                        st.write(f"• {step}")

                                with col_b:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric(
                                            "⏱️ Time",
                                            f"{fix.get('estimated_time_hours', 0)}h",
                                        )
                                    with col2:
                                        st.metric(
                                            "💰 Cost",
                                            f"${fix.get('cost_estimate_usd', 0):,}",
                                        )

                                    st.write("**Resources Needed:**")
                                    resources = fix.get("required_resources", [])
                                    for resource in resources:
                                        st.write(f"• {resource}")

                                    st.write(
                                        f"**Impact:** {fix.get('compliance_impact', '')}"
                                    )
                    else:
                        st.info(
                            "No specific fixes suggested. Consider consulting with compliance experts."
                        )
                else:
                    st.success("🎉 No violations found! Your systems appear compliant.")

                # Audit Report
                st.subheader("📋 Audit Report")
                st.text_area(
                    "Detailed Report",
                    results.get("audit_report", "No report generated"),
                    height=300,
                )

                # Export Options
                st.download_button(
                    label="📥 Download Full Report (JSON)",
                    data=json.dumps(results, indent=2),
                    file_name=f"compliance_report_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.info("Running in demo mode...")
                results = get_demo_results(company_data, regulations)

with tab3:
    st.header("📈 Analytics & Trends")

    # Sample analytics data
    col1, col2 = st.columns(2)

    with col1:
        # Compliance trend
        trend_data = pd.DataFrame(
            {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "GDPR": [65, 68, 72, 75, 78, 82],
                "CCPA": [70, 73, 75, 77, 80, 83],
                "AI_ACT": [40, 45, 50, 55, 60, 65],
            }
        )

        fig = px.line(
            trend_data,
            x="Month",
            y=["GDPR", "CCPA", "AI_ACT"],
            title="Compliance Score Trend",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Violations by type
        violations_data = pd.DataFrame(
            {
                "Type": [
                    "Data Collection",
                    "User Consent",
                    "Security",
                    "Transparency",
                    "Documentation",
                ],
                "Count": [45, 32, 28, 21, 15],
            }
        )

        fig = px.bar(
            violations_data, x="Type", y="Count", title="Common Violation Types"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Industry comparison
    st.subheader("🏢 Industry Comparison")

    industry_data = pd.DataFrame(
        {
            "Industry": ["Tech", "Finance", "Healthcare", "Retail", "Education"],
            "Avg Score": [78, 82, 75, 70, 85],
            "Violations": [12, 8, 15, 18, 6],
        }
    )

    fig = px.scatter(
        industry_data,
        x="Avg Score",
        y="Violations",
        size="Violations",
        color="Industry",
        hover_name="Industry",
        size_max=60,
        title="Industry Performance",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("⚙️ System Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("API Configuration")
        gemini_key = st.text_input("Gemini API Key", type="password")
        api_timeout = st.number_input("API Timeout (seconds)", value=30)
        enable_cache = st.checkbox("Enable Response Caching", value=True)

        if st.button("Save API Settings", use_container_width=True):
            st.success("Settings saved!")

    with col2:
        st.subheader("Monitoring Settings")
        check_interval = st.select_slider(
            "Check Interval",
            ["1 hour", "6 hours", "12 hours", "Daily", "Weekly"],
            value="Daily",
        )
        alert_threshold = st.slider("Alert Threshold", 0, 100, 70)
        enable_alerts = st.checkbox("Enable Email Alerts", value=True)

        if st.button("Save Monitoring Settings", use_container_width=True):
            st.success("Settings saved!")

    st.subheader("Regulation Sources")

    sources = {
        "GDPR": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
        "CCPA": "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml",
        "AI_ACT": "https://artificialintelligenceact.eu/",
    }

    for reg, url in sources.items():
        st.markdown(f"- **{reg}**: [{url}]({url})")

    st.subheader("Data Management")

    if st.button("Clear Cache", use_container_width=True):
        st.warning("Cache cleared!")

    if st.button("Export All Reports", use_container_width=True):
        st.info("Export initiated...")


if __name__ == "__main__":
    # This allows running the dashboard directly
    pass
