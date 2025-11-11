"""
Add AI detection results column to student_submissions table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    # Add AI detection results column
    op.add_column('student_submissions', sa.Column('ai_detection_results', JSONB, nullable=True))

def downgrade():
    # Remove AI detection results column
    op.drop_column('student_submissions', 'ai_detection_results')