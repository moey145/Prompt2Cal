#!/usr/bin/env python3
"""
Setup script for Prompt2Cal
"""

import os
import sys
import subprocess
import shutil

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_node_version():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} detected")
            return True
    except FileNotFoundError:
        pass
    print("❌ Node.js not found. Please install Node.js 16 or higher")
    return False

def setup_backend():
    """Set up the Python backend."""
    print("\n📦 Setting up Python backend...")
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file and add your OpenAI API key")
        else:
            print("⚠️  env.example not found, please create .env manually")
    
    return True

def setup_frontend():
    """Set up the React frontend."""
    print("\n📦 Setting up React frontend...")
    
    # Install Node.js dependencies
    if not run_command("cd frontend && npm install", "Installing Node.js dependencies"):
        return False
    
    return True

def main():
    """Main setup function."""
    print("🚀 Prompt2Cal Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_node_version():
        return False
    
    # Set up backend
    if not setup_backend():
        print("❌ Backend setup failed")
        return False
    
    # Set up frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Set up Google Calendar API credentials:")
    print("   - Go to Google Cloud Console")
    print("   - Enable Calendar API")
    print("   - Create OAuth 2.0 credentials")
    print("   - Download credentials.json to backend/ directory")
    print("3. Run the backend: python run_backend.py")
    print("4. Run the frontend: npm start (in frontend/ directory)")
    print("\n📖 See README.md for detailed instructions")

if __name__ == "__main__":
    main()
