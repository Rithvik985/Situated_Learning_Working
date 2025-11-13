# migrate.py - Place this in C:\Users\chitr\Desktop\spandaai\Situated_Learning\backend\
import sys
import os
import asyncio
from sqlalchemy import text

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Use the async SQLAlchemy engine exposed by database.connection
    from database.connection import async_engine as engine
    print("✓ Successfully imported database connection")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Current directory:", os.getcwd())
    print("Files in current directory:", os.listdir('.'))
    if os.path.exists('database'):
        print("Database folder contents:", os.listdir('database'))
    sys.exit(1)

async def run_migration():
    try:
        async with engine.begin() as conn:
            # Check if the column already exists
            print("Checking if assignment_id column exists...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='student_question_sets' AND column_name='assignment_id'
                """))
                
                if result.fetchone():
                    print("✓ assignment_id column already exists")
                    return
            except Exception as e:
                print(f"Note: Could not check column existence: {e}")
            
            # Add assignment_id column
            print("Adding assignment_id column to student_question_sets table...")
            await conn.execute(text("""
                ALTER TABLE student_question_sets 
                ADD COLUMN assignment_id UUID
            """))
            
            print("✓ Column added successfully!")
            
            # Add foreign key constraint
            print("Adding foreign key constraint...")
            await conn.execute(text("""
                ALTER TABLE student_question_sets 
                ADD CONSTRAINT fk_student_question_sets_assignment_id 
                FOREIGN KEY (assignment_id) REFERENCES generated_assignments(id) 
                ON DELETE SET NULL
            """))
            
            print("✓ Foreign key constraint added successfully!")
            print("✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())