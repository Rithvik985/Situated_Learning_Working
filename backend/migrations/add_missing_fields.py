"""
Migration script to create the faculty_evaluation_results table
Run this to update your PostgreSQL database schema.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/situated_learning")

def run_migration():
    """Create faculty_evaluation_results table if it doesn't exist"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            trans = conn.begin()
            print("🔧 Creating faculty_evaluation_results table...")

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS faculty_evaluation_results (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    submission_id UUID NOT NULL REFERENCES student_submissions(id) ON DELETE CASCADE,
                    faculty_id VARCHAR(255),
                    rubric_scores JSONB NOT NULL,
                    comments TEXT,
                    evaluation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Optional: create indexes for performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_faculty_eval_submission_id
                ON faculty_evaluation_results(submission_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_faculty_eval_faculty_id
                ON faculty_evaluation_results(faculty_id);
            """))

            trans.commit()
            print("✅ Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
