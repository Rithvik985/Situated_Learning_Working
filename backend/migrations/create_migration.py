# migrate.py - Place this in your backend/ directory
import sys
import os
from sqlalchemy import text

# Add the current directory to Python path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database.connection import engine
    print("✓ Successfully imported database connection")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Current directory:", os.getcwd())
    print("Files in current directory:", os.listdir('.'))
    sys.exit(1)

async def run_migration():
    try:
        async with engine.begin() as conn:
            # Check if the column already exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='student_question_sets' AND column_name='assignment_id'
            """))
            
            if result.fetchone():
                print("✓ assignment_id column already exists")
                return
            
            # Add assignment_id column
            print("Adding assignment_id column to student_question_sets table...")
            await conn.execute(text("""
                ALTER TABLE student_question_sets 
                ADD COLUMN assignment_id UUID
            """))
            
            # Add foreign key constraint
            print("Adding foreign key constraint...")
            await conn.execute(text("""
                ALTER TABLE student_question_sets 
                ADD CONSTRAINT fk_student_question_sets_assignment_id 
                FOREIGN KEY (assignment_id) REFERENCES generated_assignments(id) 
                ON DELETE SET NULL
            """))
            
            print("✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_migration())