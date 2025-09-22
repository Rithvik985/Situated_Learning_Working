#!/usr/bin/env python3
"""
Setup script for local development environment
Creates a .env file with localhost configurations
"""

import os
import shutil
from pathlib import Path

def create_local_env():
    """Create .env file for local development"""
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Error: Please run this script from the project root directory")
        return False
    
    backend_dir = Path("backend")
    env_example = backend_dir / "env.example"
    env_file = backend_dir / ".env"
    
    if not env_example.exists():
        print("❌ Error: env.example not found in backend directory")
        return False
    
    # Read the example file
    with open(env_example, 'r') as f:
        content = f.read()
    
    # Replace Docker container names with localhost
    content = content.replace("postgres:5432", "localhost:5432")
    content = content.replace("minio:9000", "localhost:9000")
    
    # Write the new .env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created backend/.env file for local development")
    print("📝 Key changes made:")
    print("   - DATABASE_URL: postgres:5432 → localhost:5432")
    print("   - MINIO_ENDPOINT: minio:9000 → localhost:9000")
    print("")
    print("🔧 Next steps:")
    print("   1. Make sure PostgreSQL is running on localhost:5432")
    print("   2. Make sure MinIO is running on localhost:9000")
    print("   3. Create database 'situated_learning_db' if it doesn't exist")
    print("   4. Run: start_separated_servers.bat (Windows) or ./start_separated_servers.sh (Linux/macOS)")
    
    return True

if __name__ == "__main__":
    create_local_env()
