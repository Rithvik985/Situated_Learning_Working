#!/usr/bin/env python3
"""
Setup script for Situated Learning System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_backend():
    """Setup backend environment"""
    print("\n📦 Setting up Backend...")
    
    # Create virtual environment
    if not os.path.exists("backend/venv"):
        if not run_command("cd backend && python -m venv venv", "Creating Python virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        pip_cmd = "backend\\venv\\Scripts\\pip"
    else:
        pip_cmd = "backend/venv/bin/pip"
    
    if not run_command(f"{pip_cmd} install -r backend/requirements.txt", "Installing Python dependencies"):
        return False
    
    # Create environment file
    env_example_path = "backend/env.example"
    env_path = "backend/.env"
    
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        shutil.copy(env_example_path, env_path)
        print("✅ Created .env file from template")
    
    # Create necessary directories
    for directory in ["backend/uploads", "backend/outputs", "backend/temp"]:
        os.makedirs(directory, exist_ok=True)
    
    return True

def setup_frontend():
    """Setup frontend environment"""
    print("\n🎨 Setting up Frontend...")
    
    # Install Node.js dependencies
    if not run_command("cd frontend && npm install", "Installing Node.js dependencies"):
        return False
    
    return True

def setup_database():
    """Setup database using Docker"""
    print("\n🗄️ Setting up Database...")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker installation"):
        print("❌ Docker is not installed or not accessible")
        return False
    
    # Start database services
    if not run_command("docker-compose up -d postgres minio redis", "Starting database services"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for database services to be ready...")
    import time
    time.sleep(10)
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Situated Learning System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("README.md") or not os.path.exists("docker-compose.yml"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    success = True
    
    # Setup backend
    if not setup_backend():
        success = False
    
    # Setup frontend
    if not setup_frontend():
        success = False
    
    # Setup database
    if not setup_database():
        success = False
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && python main.py")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Access the application at http://localhost:3000")
        print("\nOr use Docker:")
        print("docker-compose up -d")
    else:
        print("\n❌ Setup completed with errors. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
