#!/usr/bin/env python3
"""
Main runner script for Gemini Compliance Monitor
Starts both API server and dashboard
"""

import os
import subprocess
import sys
import threading
import time
import webbrowser

from dotenv import load_dotenv

load_dotenv()


def print_header():
    """Print application header"""
    header = """
    ╔══════════════════════════════════════════════════════════╗
    ║    🛡️  GEMINI COMPLIANCE MONITOR - HACKATHON EDITION    ║
    ║    Real-time AI-Powered Regulatory Compliance           ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(header)
    print(f"API Server: http://localhost:{os.getenv('API_PORT', '8000')}")
    print(f"Dashboard: http://localhost:{os.getenv('DASHBOARD_PORT', '8501')}")
    print(f"API Docs: http://localhost:{os.getenv('API_PORT', '8000')}/docs")
    print("-" * 60)


def check_api_key():
    """Check if Gemini API key is set"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ ERROR: Gemini API key not configured!")
        print("\nPlease:")
        print("1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("2. Update the .env file with your key")
        print("3. Run this script again")
        return False
    return True


def start_api_server():
    """Start FastAPI server"""
    print("🚀 Starting API server...")
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
        log_level="info",
    )


def start_dashboard():
    """Start Streamlit dashboard"""
    print("📊 Starting dashboard...")

    # Set Streamlit config
    os.environ["STREAMLIT_SERVER_PORT"] = os.getenv("DASHBOARD_PORT", "8501")
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    import streamlit.web.bootstrap
    from streamlit.web.cli import main as streamlit_main

    sys.argv = [
        "streamlit",
        "run",
        "dashboard.py",
        "--server.port",
        os.getenv("DASHBOARD_PORT", "8501"),
        "--server.address",
        "0.0.0.0",
        "--theme.base",
        "light",
        "--server.maxUploadSize",
        "50",
    ]

    streamlit.web.bootstrap.run("dashboard.py", "", [], [])


def open_browser():
    """Open browser tabs after delay"""
    time.sleep(3)
    webbrowser.open(f"http://localhost:{os.getenv('API_PORT', '8000')}/docs")
    time.sleep(1)
    webbrowser.open(f"http://localhost:{os.getenv('DASHBOARD_PORT', '8501')}")


def run_single_process():
    """Run everything in a single process (for demo)"""
    print_header()

    if not check_api_key():
        sys.exit(1)

    print("✅ Gemini API key configured")
    print("\n📋 Starting services...")

    # Start threads for API and dashboard
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
    browser_thread = threading.Thread(target=open_browser, daemon=True)

    api_thread.start()
    time.sleep(2)  # Give API time to start

    dashboard_thread.start()
    browser_thread.start()

    print("\n🎯 Services are running! Press Ctrl+C to stop.")
    print("\n📌 Quick Links:")
    print(
        f"   API Documentation: http://localhost:{os.getenv('API_PORT', '8000')}/docs"
    )
    print(f"   Dashboard: http://localhost:{os.getenv('DASHBOARD_PORT', '8501')}")
    print(f"   API Base URL: http://localhost:{os.getenv('API_PORT', '8000')}")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)


def run_separate_processes():
    """Run services in separate processes (recommended)"""
    print_header()

    if not check_api_key():
        sys.exit(1)

    print("🔧 Starting in separate processes mode...")
    print("\n1. Starting API server in background...")

    # Start API server in background
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            os.getenv("API_HOST", "0.0.0.0"),
            "--port",
            os.getenv("API_PORT", "8000"),
            "--reload",
        ]
    )

    time.sleep(3)

    print("2. Starting dashboard...")
    print(
        f"   Dashboard will open at: http://localhost:{os.getenv('DASHBOARD_PORT', '8501')}"
    )

    # Start dashboard in foreground
    dashboard_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard.py",
            "--server.port",
            os.getenv("DASHBOARD_PORT", "8501"),
            "--server.address",
            "0.0.0.0",
        ]
    )

    print("\n🎯 Both services are running!")
    print("📌 Press Ctrl+C to stop all services")

    try:
        api_process.wait()
        dashboard_process.wait()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down services...")
        api_process.terminate()
        dashboard_process.terminate()
        sys.exit(0)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--separate":
        run_separate_processes()
    else:
        run_single_process()
