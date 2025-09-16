#!/usr/bin/env python3
"""
Simple script to recreate database tables with correct schema
"""
import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_dir)

from database.connection import sync_engine
from database.models import Base

def recreate_tables():
    """Drop and recreate all tables with correct schema"""
    try:
        print("Connecting to database...")
        
        # Drop all tables and recreate them
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=sync_engine)
        
        print("Creating all tables with correct schema...")
        Base.metadata.create_all(bind=sync_engine)
        
        print("✅ Database schema recreated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Recreating database schema...")
    success = recreate_tables()
    
    if success:
        print("\n🎉 Schema fix completed!")
        print("You can now run the servers and test the evaluation system.")
    else:
        print("\n💔 Schema fix failed!")
    
    sys.exit(0 if success else 1)
