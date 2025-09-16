#!/usr/bin/env python3
"""
Database setup script for Situated Learning System
"""

import os
import sys
import subprocess
import time
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def setup_database():
    """Setup database and MinIO"""
    print("🗄️ Setting up Situated Learning Database")
    print("=" * 50)
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not accessible")
        return False
    
    # Start database services
    print("🚀 Starting database services...")
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d", "postgres", "minio", "redis"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Database services started successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start database services: {e.stderr}")
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(15)
    
    # Test database connection
    print("🔍 Testing database connection...")
    try:
        from database.connection import database, init_db
        
        # Test connection
        await database.connect()
        print("✅ Database connection successful")
        
        # Initialize database tables
        print("📊 Initializing database tables...")
        await init_db()
        print("✅ Database tables initialized")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test MinIO connection
    print("📦 Testing MinIO connection...")
    try:
        from storage.minio_client import minio_client
        minio_client.initialize_connection()
        print("✅ MinIO connection successful")
        
    except Exception as e:
        print(f"❌ MinIO connection failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\n📍 Access Points:")
    print("   • PostgreSQL: localhost:5432")
    print("   • MinIO Console: http://localhost:9001 (admin/password1234)")
    print("   • Redis: localhost:6379")
    print("\nNext steps:")
    print("1. Start upload server: python start_upload_server.py")
    print("2. Start frontend: cd frontend && npm run dev")
    
    return True

def main():
    """Main setup function"""
    try:
        success = asyncio.run(setup_database())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
