"""
Add AI detection results column to student_submissions table
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.connection import SessionLocal
from sqlalchemy import text

def add_ai_detection_column():
    """Add AI detection results column to student_submissions table"""
    db = SessionLocal()
    try:
        # Read the SQL file
        script_dir = Path(__file__).parent
        with open(script_dir / "add_ai_detection_column.sql", "r") as f:
            sql = f.read()
        
        # Execute the SQL
        print("Adding ai_detection_results column to student_submissions table...")
        db.execute(text(sql))
        db.commit()
        print("Column added successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_ai_detection_column()