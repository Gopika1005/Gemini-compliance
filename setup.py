#!/usr/bin/env python3
"""
Setup script for Gemini Compliance Monitor
Run: python setup.py
"""

import os
import platform
import subprocess
import sys


def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║      🛡️ GEMINI COMPLIANCE MONITOR SETUP              ║
    ║      Hackathon Project - Ready for Submission        ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


def create_virtual_env():
    """Create virtual environment"""
    print("\n📁 Creating virtual environment...")

    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")


def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")

    # Get pip path based on OS
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")

    # Install from requirements.txt
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print(
            "⚠️ Could not install from requirements.txt, trying individual packages..."
        )

        packages = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "google-generativeai==0.3.2",
            "streamlit==1.28.1",
            "plotly==5.17.0",
            "pandas==2.1.3",
            "requests==2.31.0",
            "python-dotenv==1.0.0",
            "sqlalchemy==2.0.23",
        ]

        for package in packages:
            print(f"Installing {package}...")
            subprocess.run([pip_path, "install", package])


def setup_environment():
    """Setup environment files"""
    print("\n⚙️ Setting up environment...")

    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env.example", "r") as f:
            example = f.read()
        with open(".env", "w") as f:
            f.write(example)
        print("✅ Created .env file from example")
    else:
        print("✅ .env file already exists")


def create_directories():
    """Create necessary directories"""
    print("\n📂 Creating directory structure...")

    directories = [
        "data/regulations",
        "data/examples",
        "data/logs",
        "static/css",
        "static/images",
        "templates",
        "tests",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created: {directory}")


def create_sample_data():
    """Create sample data files"""
    print("\n📊 Creating sample data...")

    # Sample regulation data
    sample_regulations = {
        "GDPR": {
            "name": "General Data Protection Regulation",
            "region": "EU",
            "key_requirements": [
                "Data minimization",
                "Purpose limitation",
                "Right to erasure",
                "Data protection by design",
            ],
            "max_fine_percentage": 0.04,
        },
        "CCPA": {
            "name": "California Consumer Privacy Act",
            "region": "California, USA",
            "key_requirements": [
                "Right to know",
                "Right to delete",
                "Right to opt-out",
                "Non-discrimination",
            ],
            "max_fine_percentage": 0.025,
        },
    }

    for reg_name, reg_data in sample_regulations.items():
        import json

        with open(f"data/regulations/{reg_name.lower()}.json", "w") as f:
            json.dump(reg_data, f, indent=2)

    print("✅ Sample data created")


def print_next_steps():
    """Print next steps for the user"""
    next_steps = """
    🎉 SETUP COMPLETE!
    
    Next steps:
    
    1. Get your Gemini API key:
       - Visit: https://makersuite.google.com/app/apikey
       - Create a new API key
    
    2. Update the .env file:
       - Open .env in a text editor
       - Replace "your_gemini_api_key_here" with your actual key
    
    3. Run the application:
       
       Option A - Quick Start:
       $ python run.py
       
       Option B - Separate services:
       Terminal 1: python -m uvicorn src.main:app --reload
       Terminal 2: streamlit run dashboard.py
    
    4. Access the dashboard:
       - API: http://localhost:8000
       - Dashboard: http://localhost:8501
       - API Docs: http://localhost:8000/docs
    
    5. Try the demo:
       - Use the sample company data in data/examples/
       - Test different regulations
       - Generate compliance reports
    
    For hackathon submission:
    - Update README.md with your team info
    - Add screenshots to static/images/
    - Record a demo video (2-3 minutes)
    - Prepare your pitch deck
    
    Need help? Check the docs/ folder for more information.
    """
    print(next_steps)


def main():
    """Main setup function"""
    print_banner()
    check_python_version()
    create_virtual_env()
    install_dependencies()
    setup_environment()
    create_directories()
    create_sample_data()
    print_next_steps()


if __name__ == "__main__":
    main()
