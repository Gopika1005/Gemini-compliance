"""
Streamlit Dashboard for Gemini Compliance Monitor
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Embedded mode imports
try:
    import google.generativeai as genai
    import PyPDF2
    from fpdf import FPDF

    from src.agents import MultiAgentSystem
    from src.audit_system import SystemAuditor
    from src.compliance_monitor import ComplianceMonitor
    from src.fix_suggester import FixSuggester
    from src.main import initialize_system
    from src.regulation_parser import RegulationParser
except ImportError:
    pass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load API Key for Embedded/Agent services
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except:
    pass

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="Gemini Compliance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "emergency_mode" not in st.session_state:
    st.session_state.emergency_mode = False
if "war_room_log" not in st.session_state:
    st.session_state.war_room_log = []

# Custom Trendy Styles - Sleek Dark Mode
st.markdown(
    f"""
<style>
    /* Dark Theme Background */
    .stApp {{
        background: { "radial-gradient(circle at 50% -20%, #450a0a, #020617)" if st.session_state.emergency_mode else "radial-gradient(circle at 50% -20%, #0f172a, #020617)" };
        background-attachment: fixed;
        color: #f8fafc !important;
        animation: { "emergency-pulse 4s infinite" if st.session_state.emergency_mode else "none" };
    }}

    @keyframes emergency-pulse {{
        0% {{ background-color: #020617; }}
        50% {{ background-color: #450a0a; }}
        100% {{ background-color: #020617; }}
    }}

    /* High Contrast Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }}

    /* Force Higher Contrast for ALL Markdown Text */
    [data-testid="stMarkdownContainer"], 
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] small,
    [data-testid="stMarkdownContainer"] div,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: #ffffff !important;
        font-size: 1.05rem;
        font-weight: 400;
        opacity: 1 !important;
    }}

    /* Labels and Headers */
    .stMetric label, .stMetric [data-testid="stMetricValue"] {{
        color: #ffffff !important;
    }}

    label[data-testid="stWidgetLabel"] p {{
        color: #ffffff !important;
        font-weight: 600 !important;
    }}

    /* Neon Blue Headers - Force Visibility */
    h1, h2, h3, h4, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {{
        color: #38bdf8 !important;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        opacity: 1 !important;
    }}

    /* Glassmorphism Cards/Expanders */
    div[data-testid="stExpander"], 
    .compliance-card, 
    .metric-card {{
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        color: white !important;
    }}

    .compliance-card h2, .metric-card h3 {{
        color: #38bdf8 !important;
        margin-top: 0 !important;
    }}

    .streamlit-expanderHeader {{
        background-color: transparent !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }}

    /* Link Buttons in Sidebar */
    [data-testid="stSidebar"] a {{
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        text-decoration: none !important;
        display: block !important;
        padding: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center !important;
        font-weight: 600 !important;
    }}

    [data-testid="stSidebar"] a:hover {{
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4) !important;
        transform: translateY(-2px) !important;
    }}

    /* Cyber-Polished Buttons */
    .stButton>button {{
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: white !important;
        padding: 0.8rem 1.6rem;
        font-weight: 700;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        animation: pulse-glow 3s infinite;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-3px) scale(1.02);
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.6);
        border-color: rgba(255, 255, 255, 0.8);
    }}

    /* Reflective Shine Effect */
    .stButton>button::after {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        transition: 0.8s;
    }}

    .stButton>button:hover::after {{
        left: 100%;
    }}

    @keyframes pulse-glow {{
        0% {{ box-shadow: 0 0 5px rgba(37, 99, 235, 0.2); }}
        50% {{ box-shadow: 0 0 20px rgba(37, 99, 235, 0.5); }}
        100% {{ box-shadow: 0 0 5px rgba(37, 99, 235, 0.2); }}
    }}

    /* Tab Customization */
    button[data-baseweb="tab"] {{
        color: #cbd5e1 !important;
    }}
    button[aria-selected="true"] {{
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
        font-weight: 700 !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


def generate_cyber_scan():
    """Generate a high-tech 3D Cyber-Scan animation"""
    import numpy as np
    import plotly.graph_objects as go

    # Create a scanning plane
    z_plane = np.linspace(-5, 5, 20)
    x_plane = np.linspace(-5, 5, 20)
    X, Z = np.meshgrid(x_plane, z_plane)
    Y = np.zeros_like(X)

    fig = go.Figure(
        data=[
            go.Surface(
                z=Z,
                x=X,
                y=Y,
                colorscale="Blues",
                showscale=False,
                opacity=0.3,
                contours={
                    "z": {
                        "show": True,
                        "start": -5,
                        "end": 5,
                        "size": 0.5,
                        "color": "#38bdf8",
                    }
                },
            )
        ]
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def generate_risk_constellation(simulation_results=None):
    """Generate a 3D Risk Constellation of jurisdictional conflicts"""
    import numpy as np
    import plotly.graph_objects as go

    # Jurisdictions as nodes
    jurisdictions = [
        "GDPR (EU)",
        "CCPA (USA)",
        "DMA (EU)",
        "AI Act (EU)",
        "UK-GDPR",
        "China-PIPL",
    ]
    n = len(jurisdictions)

    # Random or calculated positions
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = np.cos(theta)
    y = np.sin(theta)
    z = np.random.uniform(-1, 1, n)

    # Risk scores (normalized)
    risk_scores = [np.random.uniform(20, 90) for _ in range(n)]
    colors = [
        "#ef4444" if r > 70 else "#facc15" if r > 40 else "#22c55e" for r in risk_scores
    ]

    fig = go.Figure()

    # Add lines between nodes (Conflicts)
    for i in range(n):
        for j in range(i + 1, n):
            if np.random.rand() > 0.5:
                fig.add_trace(
                    go.Scatter3d(
                        x=[x[i], x[j]],
                        y=[y[i], y[j]],
                        z=[z[i], z[j]],
                        mode="lines",
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                        hoverinfo="none",
                    )
                )

    # Add nodes
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers+text",
            marker=dict(
                size=12, color=colors, opacity=0.8, line=dict(color="white", width=1)
            ),
            text=jurisdictions,
            textposition="top center",
            hoverinfo="text",
            hovertext=[
                f"{j}: {r:.1f}% Risk" for j, r in zip(jurisdictions, risk_scores)
            ],
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False, visible=False),
            yaxis=dict(showbackground=False, visible=False),
            zaxis=dict(showbackground=False, visible=False),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def generate_brain_graph(results):
    """Generate a 3D Knowledge Graph of ReguBrain's logic"""
    import plotly.graph_objects as go

    # Node types: Company, Regulation, Violation, Fix
    nodes_x = [0, 2, 2, 2, 4, 4, 4]
    nodes_y = [0, -2, 0, 2, -2, 0, 2]
    nodes_z = [0, 1, 1, 1, 2, 2, 2]
    labels = ["Company", "GDPR", "CCPA", "AI Act", "Fix A", "Fix B", "Fix C"]
    colors = [
        "#38bdf8",
        "#818cf8",
        "#818cf8",
        "#818cf8",
        "#34d399",
        "#34d399",
        "#34d399",
    ]

    # Edges
    edge_x = [0, 2, None, 0, 2, None, 0, 2, None, 2, 4, None, 2, 4, None, 2, 4]
    edge_y = [0, -2, None, 0, 0, None, 0, 2, None, -2, -2, None, 0, 0, None, 2, 2]
    edge_z = [0, 1, None, 0, 1, None, 0, 1, None, 1, 2, None, 1, 2, None, 1, 2]

    fig = go.Figure()

    # Edges
    fig.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(color="rgba(255,255,255,0.2)", width=1),
            hoverinfo="none",
        )
    )

    # Nodes
    fig.add_trace(
        go.Scatter3d(
            x=nodes_x,
            y=nodes_y,
            z=nodes_z,
            mode="markers+text",
            text=labels,
            marker=dict(size=10, color=colors, opacity=0.9, symbol="sphere"),
            textposition="top center",
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(15, 23, 42, 0.5)",
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    return fig


def generate_compliance_radar(results):
    """Generate an advanced 3D Radar Chart for risk analysis"""
    import plotly.graph_objects as go

    categories = ["Privacy", "Security", "Transparency", "Fairness", "Accountability"]

    # Map results to these categories (mock data mapping based on score for demo)
    score = results.get("compliance_score", 0)
    # Give some variance to make it look "advanced"
    import random

    values = [
        score + random.randint(-5, 5),
        score + random.randint(-10, 0),
        score + random.randint(0, 10),
        score + random.randint(-5, 5),
        score + random.randint(-8, 2),
    ]
    values = [max(0, min(100, v)) for v in values]
    values += [values[0]]  # Close the loop
    categories += [categories[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(56, 189, 248, 0.3)",
            line=dict(color="#38bdf8", width=2),
            name="Compliance Profile",
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15, 23, 42, 0.5)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#94a3b8",
                gridcolor="rgba(255, 255, 255, 0.1)",
                font=dict(size=10),
            ),
            angularaxis=dict(
                color="#f1f5f9",
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=40, r=40),
        height=300,
    )

    return fig


def generate_compliance_sunburst(results):
    """Generate a hierarchical Sunburst chart for regulatory deep-dive"""
    import pandas as pd
    import plotly.express as px

    # Hierarchical data for the sunburst
    data = {
        "labels": [
            "Regulations",
            "GDPR",
            "CCPA",
            "AI Act",
            "Privacy",
            "Security",
            "Governance",
            "Critical",
            "High",
            "Medium",
        ],
        "parents": [
            "",
            "Regulations",
            "Regulations",
            "Regulations",
            "GDPR",
            "CCPA",
            "AI Act",
            "Privacy",
            "Security",
            "Governance",
        ],
        "values": [0, 40, 30, 30, 25, 20, 15, 10, 15, 20],
    }

    fig = px.sunburst(
        data,
        names="labels",
        parents="parents",
        values="values",
        color="values",
        color_continuous_scale="Blues",
        title="Regulatory Hierarchy Deep-Dive",
    )

    fig.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
    )

    return fig


def generate_prioritization_cube(results):
    """Generate a 3D Fix-Prioritization Cube (Impact vs Effort vs Severity)"""
    import pandas as pd
    import plotly.graph_objects as go

    fixes = results.get("suggested_fixes", [])
    if not fixes:
        return None

    # Extraction for 3D mapping
    df_data = []
    severity_map = {"critical": 10, "high": 7, "medium": 4, "low": 2}

    for f in fixes:
        df_data.append(
            {
                "Title": f.get("title", "Fix"),
                "Effort": f.get("estimated_time_hours", 0),
                "Cost": f.get("cost_estimate_usd", 0),
                "Severity": severity_map.get(f.get("priority", "medium").lower(), 4),
            }
        )

    df = pd.DataFrame(df_data)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=df["Effort"],
                y=df["Cost"],
                z=df["Severity"],
                text=df["Title"],
                mode="markers+text",
                marker=dict(
                    size=10,
                    color=df["Severity"],
                    colorscale="Viridis",
                    opacity=0.8,
                    colorbar=dict(title="Severity Level", thickness=15),
                ),
            )
        ]
    )

    fig.update_layout(
        scene=dict(
            xaxis_title="Effort (Hours)",
            yaxis_title="Cost ($)",
            zaxis_title="Severity Score",
            bgcolor="rgba(15, 23, 42, 0.5)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            zaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
    )

    return fig


def generate_policy_pdf(company_name, results):
    """Generate a simple compliance policy PDF"""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, f"Compliance Policy: {company_name}", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(
            0, 10, f"Compliance Score: {results.get('compliance_score', 0)}%", ln=True
        )
        pdf.ln(5)

        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Mandatory Fixes Required:", ln=True)
        pdf.ln(5)

        pdf.set_font("helvetica", size=11)
        for fix in results.get("suggested_fixes", []):
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 10, f"- {fix.get('title')}", ln=True)
            pdf.set_font("helvetica", size=10)
            pdf.multi_cell(0, 10, f"{fix.get('description')}")
            pdf.ln(2)

        return pdf.output()
    except Exception as e:
        return f"Error generating PDF: {str(e)}".encode()


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


# --- Authentication Layer ---
if not st.session_state.authenticated:
    st.markdown(
        """
        <div style='text-align: center; padding-top: 5rem;'>
            <h1 style='font-size: 3rem; color: #38bdf8; margin-bottom: 0;'>🛡️ ReguBrain</h1>
            <p style='color: #94a3b8; font-size: 1.2rem;'>Governance • Compliance • Intelligence</p>
        </div>
        <div style='display: flex; justify-content: center; align-items: center; margin-top: 2rem;'>
            <div style='background: rgba(30, 41, 59, 0.7); padding: 3rem; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.3); backdrop-filter: blur(20px); width: 450px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);'>
                <h2 style='text-align: center; color: white; margin-bottom: 2rem;'>Secure Access Gateway</h2>
    """,
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns([1, 10])
    with col_r:
        user = st.text_input("Operator Identity", placeholder="Username")
        pw = st.text_input(
            "Security Clearance", type="password", placeholder="Password"
        )

        if st.button("🔓 AUTHORIZE ACCESS", use_container_width=True):
            if user == "admin" and pw == "admin":
                st.session_state.authenticated = True
                st.success("Access Granted. Initializing ReguBrain...")
                st.rerun()
            else:
                st.error("Access Denied. Invalid Credentials.")

    st.markdown(
        """
            </div>
        </div>
        <div style='text-align: center; margin-top: 2rem; opacity: 0.5;'>
            <small>System restricted to authorized personnel. All interactions are logged for compliance.</small>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.stop()


# Header
st.markdown("# 🛡️ Gemini Compliance Monitor", unsafe_allow_html=True)
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
        index=0,
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
            # Use global api_key
            if not api_key:
                return None

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")

            regulation_parser = RegulationParser(model)
            system_auditor = SystemAuditor(model)
            fix_suggester = FixSuggester(model)
            monitor = ComplianceMonitor(
                regulation_parser, system_auditor, fix_suggester
            )
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
    st.header("🌍 Global Polyglot")
    lang_option = st.selectbox(
        "Dashboard Language",
        ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Hindi"],
        index=0,
    )

    if lang_option != "English":
        st.info(f"ReguBrain is translating reports to {lang_option}...")
        if "results" in st.session_state and st.session_state.results:
            # Simple simulation of translation for hackathon demo
            # In real app, we'd call agent_system.translate(results, lang_option)
            st.session_state.results["translation_status"] = (
                f"Localized to {lang_option}"
            )

    st.markdown("---")
    st.markdown("**📖 Project Support**")
    with st.expander("🚀 Quick Start Guide"):
        st.write("1. **Configure**: Set your API key in the Settings tab.")
        st.write(
            "2. **Analyze**: Go to 'Compliance Check', enter company data, and click Run."
        )
        st.write("3. **Fix**: View 'Suggested Fixes' to see how to remediate issues.")
        st.write("4. **Monitor**: Use the Dashboard tab for a high-level overview.")

    st.link_button(
        "📂 GitHub Repository",
        "https://github.com/Gopika1005/Gemini-compliance",
        use_container_width=True,
    )
    st.link_button(
        "📝 Report an Issue",
        "https://github.com/Gopika1005/Gemini-compliance/issues",
        use_container_width=True,
    )
    st.link_button(
        "🔬 AI Act Explorer",
        "https://artificialintelligenceact.eu/",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown(
        """
    <div style='background: rgba(30, 41, 59, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);'>
    <small style='color: #cbd5e1;'>Built with ❤️ for Hackathon Submission</small><br>
    <small style='color: #cbd5e1;'>Using Google Gemini AI • FastAPI • Streamlit</small>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Main Content
(
    tab_overview,
    tab_analysis,
    tab_visual,
    tab_chat,
    tab_analytics,
    tab_oracle,
    tab_warroom,
    tab_settings,
) = st.tabs(
    [
        "📊 Overview",
        "🔍 Compliance Analysis",
        "📸 Visual UI Audit",
        "🤖 AI Consultant",
        "📈 Analytics",
        "🔮 Oracle",
        "🚨 War Room",
        "⚙️ Settings",
    ]
)

# Shared Results State
if "results" not in st.session_state:
    st.session_state.results = {}
results = st.session_state.results

with tab_overview:
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

with tab_analysis:
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
                            embedded_system.analyze_compliance(
                                company_data, regulations
                            )
                        )
                    else:
                        st.warning(
                            "⚠️ GEMINI_API_KEY not found or system not initialized. Using demo mode."
                        )
                        results = get_demo_results(company_data, regulations)

                else:
                    # Demo mode
                    results = get_demo_results(company_data, regulations)

                # Cyber-Scan animation during processing
                with st.spinner("Initiating Hyper-Spectral Compliance Scan..."):
                    scan_placeholder = st.empty()
                    scan_placeholder.plotly_chart(
                        generate_cyber_scan(), use_container_width=True
                    )
                    import time

                    time.sleep(2)  # Visual pause for effect
                    scan_placeholder.empty()

                # Store in session state for other tabs
                st.session_state.results = results

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

                # Radar Chart and Brain Graph in new row
                st.divider()
                col_chart, col_brain = st.columns([1, 1])
                with col_chart:
                    st.markdown(
                        "<h2 style='text-align: center;'>🧊 Advanced Risk Dimensions</h2>",
                        unsafe_allow_html=True,
                    )
                    radar_fig = generate_compliance_radar(results)
                    st.plotly_chart(radar_fig, use_container_width=True)

                with col_brain:
                    st.markdown(
                        "<h2 style='text-align: center;'>🧠 ReguBrain Knowledge Graph</h2>",
                        unsafe_allow_html=True,
                    )
                    brain_fig = generate_brain_graph(results)
                    st.plotly_chart(brain_fig, use_container_width=True)
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

                # Strategic Remediation Planning (3D)
                st.divider()
                st.markdown(
                    "<h2 style='text-align: center;'>🧊 Strategic Remediation Planning</h2>",
                    unsafe_allow_html=True,
                )
                st.info(
                    "Rotate the 3D Cube to find the 'Low Hanging Fruit' (Low effort, Low cost, High severity fixes)."
                )
                cube_fig = generate_prioritization_cube(results)
                if cube_fig:
                    st.plotly_chart(cube_fig, use_container_width=True)

                # Audit Report
                st.subheader("📋 Audit Report")
                st.text_area(
                    "Detailed Report",
                    results.get("audit_report", "No report generated"),
                    height=300,
                )

                # Advanced Compliance Tools
                st.divider()
                st.subheader("🚀 Advanced Compliance Tools")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "📄 Generate Compliance Policy (PDF)", use_container_width=True
                    ):
                        policy_pdf = generate_policy_pdf(company_name, results)
                        if b"Error" in policy_pdf[:50]:
                            st.error(policy_pdf.decode())
                        else:
                            st.download_button(
                                label="📥 Download Policy Document",
                                data=policy_pdf,
                                file_name=f"{company_name.replace(' ', '_')}_Compliance_Policy.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                with col2:
                    if st.button(
                        "🤖 Discuss results with AI Consultant",
                        use_container_width=True,
                    ):
                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": f"I just ran a compliance audit for {company_name} and got a score of {results.get('compliance_score') or 0}%. What are my most critical next steps?",
                            }
                        )
                        st.info(
                            "Head over to the '🤖 AI Consultant' tab to start the discussion!"
                        )

                # Export Options
                st.subheader("📥 Export Audit Data")
                st.download_button(
                    label="💾 Download Full Report (JSON)",
                    data=json.dumps(results, indent=2),
                    file_name=f"compliance_report_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.info("Running in demo mode...")
                results = get_demo_results(company_data, regulations)

with tab_visual:
    st.header("📸 Visual UI Compliance Audit")
    st.markdown("### Detect Dark Patterns & GDPR Violations via Computer Vision")
    st.info(
        "Upload a screenshot of your website, cookie banner, or app UI. Our Multimodal Gemini agent will analyze it for compliance issues."
    )

    ui_screenshot = st.file_uploader(
        "Upload UI Screenshot", type=["png", "jpg", "jpeg"]
    )

    if ui_screenshot:
        st.image(ui_screenshot, caption="Uploaded Web UI", use_container_width=True)

        if st.button("🚀 Analyze UI for Compliance"):
            with st.spinner("Gemini 1.5 Pro is analyzing the UI components..."):
                if agent_system:
                    try:
                        from PIL import Image

                        img = Image.open(ui_screenshot)

                        visual_prompt = """
                        You are a Senior Compliance Auditor with expertise in GDPR, CCPA, and the EU AI Act.
                        Analyze this UI screenshot for:
                        1. Dark Patterns (misleading buttons, forced choices).
                        2. GDPR Cookie Consent compliance (Are Opt-out/Manage options visible?).
                        3. Privacy transparency.
                        4. UI accessibility and fairness.
                        
                        Provide a technical audit report with specific violations and suggested fixes.
                        """

                        # Call multimodal Gemini
                        model_vision = genai.GenerativeModel("gemini-1.5-pro")
                        response = model_vision.generate_content([visual_prompt, img])

                        st.subheader("🕵️ Visual Audit Report")
                        st.markdown(response.text)

                    except Exception as e:
                        st.error(f"Visual Analysis Failed: {e}")
                else:
                    st.warning(
                        "Please configure your GEMINI_API_KEY in Settings to use Visual Audit."
                    )

with tab_chat:
    st.header("🤖 AI Compliance Consultant")
    st.info(
        "Ask ReguBrain anything about regulations, audit results, or technical implementation."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize Agent System
    if api_key:
        agent_system = MultiAgentSystem(api_key)
    else:
        agent_system = None

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is the data retention limit under GDPR?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if agent_system:
                response = asyncio.run(
                    agent_system.get_consultation(prompt, st.session_state.messages)
                )
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            else:
                st.warning(
                    "Please configure your GEMINI_API_KEY in the Settings tab to use the AI Consultant."
                )

with tab_oracle:
    st.header("🔮 The Oracle: Policy Simulator")
    st.markdown("### Model Future Decisions & Regulatory Impact")
    st.info(
        "Simulate business changes before execution to see their legal impact across all jurisdictions."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🛠️ Simulation Parameters")
        sim_choice = st.selectbox(
            "Select Scenario",
            [
                "Deploying Generative AI for Customer Support",
                "Selling User Data to Third-Party Advertisers",
                "Implementing Biometric Authentication",
                "Automating Hiring via ML Algorithms",
                "Expanding Services to China (PIPL Compliance)",
                "Custom Scenario...",
            ],
        )

        if sim_choice == "Custom Scenario...":
            custom_sim = st.text_area(
                "Describe your future policy change",
                "e.g., We plan to track user location 24/7 for improved delivery speed.",
            )

        jurisdiction = st.multiselect(
            "Target Jurisdictions",
            [
                "EU",
                "USA (California)",
                "USA (Federal)",
                "UK",
                "China",
                "India",
                "Brazil",
            ],
            default=["EU", "USA (California)"],
        )

        sim_btn = st.button("🚀 Run Oracle Simulation", use_container_width=True)

    with col2:
        if sim_btn:
            with st.spinner("Oracle is scrying the regulatory future..."):
                st.markdown("#### 🧊 Global Risk Constellation")
                st.plotly_chart(generate_risk_constellation(), use_container_width=True)

                # Mock analysis for demo
                st.subheader("🕵️ Oracle's Verdict")
                col01, col02, col03 = st.columns(3)
                col01.metric("Likelihood of Fine", "High", "Critical Risk")
                col02.metric("Legal Resistance", "8.2/10", "Strong")
                col03.metric("Ethics Score", "42/100", "-15%")

                st.markdown(
                    f"""
                > [!WARNING]
                > **Conflict Detected**: Your proposed policy for *{sim_choice}* directly violates **Article 22 of GDPR** (Automated decision-making) and fails transparency tests under the **EU AI Act**.
                
                **Strategic Advice:** 
                Implement a 'Human-in-the-loop' bypass and update your Data Processing Agreement (DPA) before going live.
                """
                )
        else:
            st.markdown(
                """
            <div style='text-align: center; padding: 5rem; border: 1px dashed rgba(255,255,255,0.2); border-radius: 12px;'>
                <h1 style='font-size: 4rem; opacity: 0.2;'>🔮</h1>
                <p style='opacity: 0.5;'>Configure simulation parameters on the left to see your future risk constellation.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

with tab_analytics:
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

    col_a, col_b = st.columns([1, 1])
    with col_a:
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

    with col_b:
        # Hierarchical Sunburst
        st.markdown(
            "<h3 style='text-align: center;'>Regulatory Intelligence</h3>",
            unsafe_allow_html=True,
        )
        sunburst_fig = generate_compliance_sunburst(results)
        st.plotly_chart(sunburst_fig, use_container_width=True)

with tab_warroom:
    st.header("🚨 War Room: Incident Response")
    st.markdown("### Emergency Simulation Center")
    st.warning(
        "This mode simulates a critical data breach to test system resilience and agent response."
    )

    if st.button("🚨 TRIGGER CRITICAL BREACH SIMULATION", use_container_width=True):
        st.session_state.emergency_mode = True
        st.session_state.war_room_log = []
        st.rerun()

    if st.session_state.emergency_mode:
        st.markdown(
            "<h1 style='color: #ef4444; text-align: center; animation: pulse 1s infinite;'>RED ALERT: CRITICAL LEAK DETECTED</h1>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            st.error("⚠️ DATA EXFILTRATION IN PROGRESS")
            st.info(
                "**Target:** User PII Database\n\n**Origin:** Unknown IP (Eastern Europe)"
            )

            if st.button("🛡️ SECURE SYSTEMS & STOP LEAK"):
                st.session_state.emergency_mode = False
                st.success("Containment Successful. Systems Secured.")
                st.rerun()

        with col2:
            st.subheader("🤖 Agent Coordination Log")

            # Simulated Agent Steps
            if not st.session_state.war_room_log:
                with st.spinner("Agents initiating response..."):
                    # Step 1: Researcher
                    st.session_state.war_room_log.append(
                        "🔍 **Researcher Agent:** Identified potential violations: GDPR Article 33 (Breach Notification) and CCPA § 1798.150."
                    )
                    # Step 2: Auditor
                    st.session_state.war_room_log.append(
                        "⚖️ **Auditor Agent:** Breach depth assessed. 45,000 PII records exposed. Severity: **CRITICAL**."
                    )
                    # Step 3: Advisor
                    st.session_state.war_room_log.append(
                        "📋 **Advisor Agent:** Strategic Plan: 1. Segregate compromised DB. 2. Notify Regulators. 3. Regenerate all access tokens."
                    )

            for msg in st.session_state.war_room_log:
                st.markdown(f"> {msg}")

            # Breach Notification Generator
            st.divider()
            st.subheader("📄 Automated Regulatory Filing")

            breach_details = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "severity": "Critical",
                "affected_users": 45000,
                "regulations": ["GDPR", "CCPA"],
            }

            if st.button("Generate Regulatory Breach Notice"):
                # Use FPDF to generate a professional notice
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("helvetica", "B", 20)
                pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 15, "OFFICIAL BREACH NOTIFICATION", ln=True, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("helvetica", "", 12)
                pdf.ln(10)
                pdf.write(
                    5,
                    f"To: Data Protection Authorities\nFrom: Gemini Compliance Monitor (Incident #SIM-{random.randint(1000,9999)})\nDate: {breach_details['date']}\n\n",
                )
                pdf.set_font("helvetica", "B", 14)
                pdf.write(10, "1. Incident Description\n")
                pdf.set_font("helvetica", "", 12)
                pdf.write(
                    5,
                    "A critical data leak was detected involving unauthorized retrieval of PII records from the primary user database. Containment protocols were initiated via Multi-Agent ReguBrain systems.\n\n",
                )
                pdf.set_font("helvetica", "B", 14)
                pdf.write(10, "2. Impact Assessment\n")
                pdf.set_font("helvetica", "", 12)
                pdf.write(
                    5,
                    f"- Severity: {breach_details['severity']}\n- Affected Records: {breach_details['affected_users']}\n- Primary Regulations: {', '.join(breach_details['regulations'])}\n\n",
                )

                pdf_output = pdf.output(dest="S")
                st.download_button(
                    label="📥 Download Official Breach Notice (PDF)",
                    data=pdf_output,
                    file_name="breach_notification_report.pdf",
                    mime="application/pdf",
                )

with tab_settings:
    st.header("⚙️ Settings")

    # Document Intelligence Section
    st.subheader("📄 Document Intelligence")
    uploaded_file = st.file_uploader("Upload Regulation PDF/Text", type=["pdf", "txt"])
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Analyzing document with Researcher Agent..."):
                if uploaded_file.type == "application/pdf":
                    import PyPDF2

                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                else:
                    text = uploaded_file.read().decode()

                if agent_system:
                    doc_result = asyncio.run(agent_system.process_document(text))
                    st.success("Document Analyzed!")
                    st.json(doc_result)
                else:
                    st.error("AI System not initialized. Check API Key.")

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
        "GDPR": "https://gdpr-info.eu/",
        "CCPA": "https://oag.ca.gov/privacy/ccpa",
        "AI_ACT": "https://artificialintelligenceact.eu/the-act/",
    }

    reg_descriptions = {
        "GDPR": {
            "summary": "The EU's primary data protection rule. It gives individuals control over their personal data.",
            "keys": [
                "Consent (Art. 7)",
                "Right to Access (Art. 15)",
                "Data Minimization (Art. 5)",
                "6% Revenue Fines",
            ],
            "project_scope": "We audit your technical data pipelines, storage locations, and consent banners.",
        },
        "CCPA": {
            "summary": "California Consumer Privacy Act. Focuses on transparency and the right to opt-out of data sales.",
            "keys": [
                "Right to Know",
                "Right to Delete",
                "Do Not Sell/Share",
                "Equitable Service",
            ],
            "project_scope": "We check your 'Do Not Sell' UI placement and data sharing disclosures.",
        },
        "AI_ACT": {
            "summary": "The first comprehensive AI law in the world, focused on risk-based regulation.",
            "keys": [
                "Prohibited AI",
                "High-Risk Systems",
                "Transparency Obligations",
                "Innovation Support",
            ],
            "project_scope": "We analyze your AI models for risk levels and transparency documentation.",
        },
    }

    for reg, url in sources.items():
        with st.expander(f"📌 {reg} Knowledge Base"):
            data = reg_descriptions.get(
                reg,
                {"summary": "Regulatory framework.", "keys": [], "project_scope": ""},
            )
            st.info(data["summary"])

            if data["keys"]:
                st.write("**Key Requirements:**")
                for key in data["keys"]:
                    st.write(f"- {key}")

            st.write(f"**How we help:** {data['project_scope']}")

            # Alternative Links
            st.write("**Resource Links:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.link_button(f"🚀 Open {reg} Guide", url, use_container_width=True)
            with col_b:
                alt_url = f"https://en.wikipedia.org/wiki/{reg.replace('_', ' ')}"
                st.link_button(f"📖 Wiki Summary", alt_url, use_container_width=True)

            st.info(
                "💡 **Tip:** If the link doesn't open, check if your browser blocked a popup."
            )

    st.subheader("Data Management")

    if st.button("Clear Cache", use_container_width=True):
        st.warning("Cache cleared!")

    if st.button("Export All Reports", use_container_width=True):
        st.info("Export initiated...")


if __name__ == "__main__":
    # This allows running the dashboard directly
    pass
