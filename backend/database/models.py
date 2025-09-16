"""
SQLAlchemy models for Situated Learning System
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, BigInteger, ForeignKey, UniqueConstraint, CheckConstraint, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .connection import Base

class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    past_assignments = relationship("PastAssignment", back_populates="course")
    generated_assignments = relationship("GeneratedAssignment", back_populates="course")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('title', 'course_code', 'academic_year', 'semester', name='unique_course'),
        CheckConstraint('semester IN (1, 2)', name='check_semester'),
    )

class PastAssignment(Base):
    """Past assignment model"""
    __tablename__ = "past_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    original_file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger)
    processing_status = Column(String(50), default='pending')
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="past_assignments")
    questions = relationship("AssignmentQuestion", back_populates="assignment")

class AssignmentQuestion(Base):
    """Assignment question model"""
    __tablename__ = "assignment_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("past_assignments.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text)
    extracted_content = Column(Text)
    partitioned_file_path = Column(String(500))
    has_images = Column(Boolean, default=False)
    processing_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignment = relationship("PastAssignment", back_populates="questions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('assignment_id', 'question_number', name='unique_assignment_question'),
    )

class GeneratedAssignment(Base):
    """Generated assignment model"""
    __tablename__ = "generated_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_name = Column(String(255), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(ARRAY(Text))
    industry_context = Column(Text)
    estimated_time = Column(Integer)
    difficulty_level = Column(String(50))
    class_numbers = Column(ARRAY(Integer))
    topics = Column(ARRAY(Text))
    domains = Column(ARRAY(Text))
    custom_instructions = Column(Text)
    tags = Column(ARRAY(Text), default=['AI-Generated'])
    version = Column(Integer, default=1)
    parent_assignment_id = Column(UUID(as_uuid=True), ForeignKey("generated_assignments.id"))
    reason_for_change = Column(Text)
    is_selected = Column(Boolean, default=False)
    assignment_name = Column(String(255))
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="generated_assignments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')", name='check_difficulty_level'),
    )

class AssignmentRubric(Base):
    """Assignment rubric model"""
    __tablename__ = "assignment_rubrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    rubric_name = Column(String(255), nullable=False)
    doc_type = Column(String(100), default='Assignment')
    criteria = Column(JSONB, nullable=False)
    total_points = Column(Integer)
    is_edited = Column(Boolean, default=False)
    reason_for_edit = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class StudentSubmission(Base):
    """Student submission model"""
    __tablename__ = "student_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("generated_assignments.id", ondelete="CASCADE"), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger)
    processing_status = Column(String(50), default='pending')  # pending, processed, failed
    extraction_method = Column(String(50))  # standard, ocr, ocr_vision_llm, standard_fallback
    extracted_text = Column(Text)
    ocr_confidence = Column(Float)
    processing_metadata = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assignment = relationship("GeneratedAssignment")
    evaluation_results = relationship("EvaluationResult", back_populates="submission")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("processing_status IN ('pending', 'processed', 'failed')", name='check_processing_status'),
        CheckConstraint("extraction_method IN ('standard', 'ocr', 'ocr_vision_llm', 'standard_fallback')", name='check_extraction_method'),
    )

class EvaluationResult(Base):
    """Evaluation result model"""
    __tablename__ = "evaluation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("generated_assignments.id", ondelete="CASCADE"), nullable=False)
    rubric_id = Column(UUID(as_uuid=True), ForeignKey("assignment_rubrics.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    criterion_scores = Column(JSONB)  # Detailed scores per criterion
    ai_feedback = Column(Text)
    faculty_feedback = Column(Text)
    faculty_score_adjustment = Column(Float)
    faculty_reason = Column(Text)
    flags = Column(ARRAY(Text))  # quality_issues, plagiarism_detected, etc.
    evaluation_metadata = Column(JSONB)
    faculty_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    submission = relationship("StudentSubmission", back_populates="evaluation_results")
    assignment = relationship("GeneratedAssignment")
    rubric = relationship("AssignmentRubric")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("overall_score >= 0", name='check_overall_score_positive'),
    )