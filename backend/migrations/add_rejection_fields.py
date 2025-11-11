"""
Migration script: Add rejection-related fields to student_submissions table
"""
from sqlalchemy import inspect, text
from database.connection import sync_engine

def upgrade_database():
    """Add rejection_reason, rejection_date, and faculty_feedback columns if they don't exist."""
    inspector = inspect(sync_engine)
    columns = [col['name'] for col in inspector.get_columns('student_submissions')]

    with sync_engine.connect() as conn:
        if 'rejection_reason' not in columns:
            conn.execute(text('ALTER TABLE student_submissions ADD COLUMN rejection_reason TEXT'))
            print("✅ Added column: rejection_reason")

        if 'rejection_date' not in columns:
            conn.execute(text('ALTER TABLE student_submissions ADD COLUMN rejection_date TIMESTAMPTZ'))
            print("✅ Added column: rejection_date")

        if 'faculty_feedback' not in columns:
            conn.execute(text('ALTER TABLE student_submissions ADD COLUMN faculty_feedback TEXT'))
            print("✅ Added column: faculty_feedback")

        conn.commit()

if __name__ == "__main__":
    upgrade_database()
    print("🎉 Migration completed successfully.")
