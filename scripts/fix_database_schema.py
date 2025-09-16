#!/usr/bin/env python3
"""
Script to fix the database schema issue with course_id type mismatch
"""
import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_dir)

from sqlalchemy import text
from database.connection import sync_engine, SyncSessionLocal
from database.models import Base, Course

def fix_database_schema():
    """Fix the course_id type mismatch in generated_assignments table"""
    engine = sync_engine
    
    try:
        print("Connecting to database...")
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("Checking current schema...")
                
                # Check if generated_assignments table exists and what type course_id is
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'generated_assignments' 
                    AND column_name = 'course_id'
                """))
                
                current_schema = result.fetchone()
                if current_schema:
                    print(f"Current course_id type: {current_schema[1]}")
                    
                    if current_schema[1] != 'uuid':
                        print("Fixing course_id type mismatch...")
                        
                        # Drop dependent tables first
                        print("Dropping dependent tables...")
                        conn.execute(text("DROP TABLE IF EXISTS evaluation_results CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS student_submissions CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS assignment_rubrics CASCADE"))
                        conn.execute(text("DROP TABLE IF EXISTS generated_assignments CASCADE"))
                        
                        print("Recreating tables with correct schema...")
                        
                        # Commit the drop operations first
                        trans.commit()
                        
                        # Start a new transaction for table creation
                        trans = conn.begin()
                        
                        # Recreate all tables with correct schema
                        Base.metadata.create_all(engine)
                        
                        # Insert some sample data
                        print("Inserting sample data...")
                        
                        # First, ensure we have some courses
                        courses_result = conn.execute(text("SELECT COUNT(*) FROM courses"))
                        course_count = courses_result.scalar()
                        
                        if course_count == 0:
                            print("No courses found. Please run the upload server first to create some courses.")
                        else:
                            # Insert sample assignments
                            conn.execute(text("""
                                INSERT INTO generated_assignments (
                                    course_id, 
                                    course_name, 
                                    title, 
                                    description, 
                                    difficulty_level,
                                    topics,
                                    domains,
                                    assignment_name,
                                    is_selected
                                ) 
                                SELECT 
                                    c.id,
                                    c.title,
                                    'Sample Assignment for ' || c.title,
                                    'This is a sample assignment generated for testing the evaluation system.',
                                    'Intermediate',
                                    ARRAY['Programming', 'Problem Solving'],
                                    ARRAY['Computer Science'],
                                    'Sample_Assignment_' || c.course_code,
                                    true
                                FROM courses c
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM generated_assignments ga WHERE ga.course_id = c.id
                                )
                                LIMIT 3
                            """))
                            
                            # Insert sample rubrics
                            conn.execute(text("""
                                INSERT INTO assignment_rubrics (
                                    assignment_ids,
                                    rubric_name,
                                    doc_type,
                                    criteria
                                )
                                SELECT 
                                    ARRAY[ga.id],
                                    ga.assignment_name || '_Rubric',
                                    'Assignment',
                                    '{"rubrics": [{"criteria": "Technical Implementation", "questions": ["Is the code functional?", "Are best practices followed?", "Is the solution efficient?", "Is error handling implemented?", "Is the code well-documented?"]}, {"criteria": "Problem Understanding", "questions": ["Is the problem correctly understood?", "Are all requirements addressed?", "Is the approach appropriate?", "Are edge cases considered?", "Is the solution complete?"]}, {"criteria": "Code Quality", "questions": ["Is the code readable?", "Is the code maintainable?", "Are naming conventions followed?", "Is the code structure logical?", "Are comments meaningful?"]}, {"criteria": "Testing and Validation", "questions": ["Are test cases included?", "Is the solution validated?", "Are different scenarios tested?", "Is error handling tested?", "Are results verified?"]}]}'::jsonb
                                FROM generated_assignments ga
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM assignment_rubrics ar WHERE ar.assignment_ids @> ARRAY[ga.id]
                                )
                                LIMIT 3
                            """))
                        
                        print("Schema fix completed successfully!")
                    else:
                        print("Schema is already correct!")
                else:
                    print("Table generated_assignments not found, creating all tables...")
                    Base.metadata.create_all(engine)
                    print("Tables created successfully!")
                
                # Commit the transaction
                trans.commit()
                print("Database schema fix completed!")
                
            except Exception as e:
                trans.rollback()
                print(f"Error during schema fix: {e}")
                raise
                
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Make sure PostgreSQL is running and the database exists.")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting database schema fix...")
    success = fix_database_schema()
    if success:
        print("✅ Database schema fixed successfully!")
        sys.exit(0)
    else:
        print("❌ Database schema fix failed!")
        sys.exit(1)
