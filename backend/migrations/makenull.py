"""
Migration Script: Make faculty_id column nullable in faculty_evaluation_results
Usage: python make_faculty_id_nullable.py
"""
import os
from sqlalchemy import create_engine, text

# 🧩 Update this with your actual DB credentials or read from env
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/situated_learning')

def make_faculty_id_nullable():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        try:
            print("🔄 Running migration: making faculty_id nullable...")
            connection.execute(text("""
                ALTER TABLE faculty_evaluation_results
                MODIFY COLUMN faculty_id CHAR(36) NULL;
            """))
            connection.commit()
            print("✅ Migration successful: faculty_id is now nullable.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
        finally:
            connection.close()

if __name__ == "__main__":
    make_faculty_id_nullable()
