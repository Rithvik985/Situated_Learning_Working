"""Add submission processing fields migration

This migration adds fields for document processing features to the student_submissions table:
- original_file_name
- extraction_method
- extracted_text
- ocr_confidence
- processing_metadata
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from backend.database.connection import sync_engine

def run_migration():
    with sync_engine.connect() as connection:
        # Add original_file_name column
        connection.execute(text("""
            ALTER TABLE student_submissions 
            ADD COLUMN IF NOT EXISTS original_file_name VARCHAR(255)
        """))
        
        # Add extraction_method column
        connection.execute(text("""
            ALTER TABLE student_submissions 
            ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50)
        """))
        
        # Add extracted_text column
        connection.execute(text("""
            ALTER TABLE student_submissions 
            ADD COLUMN IF NOT EXISTS extracted_text TEXT
        """))
        
        # Add ocr_confidence column
        connection.execute(text("""
            ALTER TABLE student_submissions 
            ADD COLUMN IF NOT EXISTS ocr_confidence FLOAT
        """))
        
        # Add processing_metadata column
        connection.execute(text("""
            ALTER TABLE student_submissions 
            ADD COLUMN IF NOT EXISTS processing_metadata JSONB
        """))
        
        connection.commit()

if __name__ == "__main__":
    run_migration()