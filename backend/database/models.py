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
    student_question_sets = relationship("StudentQuestionSet", back_populates="course")


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
    
    # ADD THIS RELATIONSHIP - CRITICAL
    student_question_sets = relationship("StudentQuestionSet", back_populates="assignment")
    
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
    """Student submission of an assignment"""
    __tablename__ = "student_submissions"
    
    # Add AI detection results column
    ai_detection_results = Column(JSONB, nullable=True)
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(255), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("generated_assignments.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    original_file_name = Column(String(255), nullable=True)  # Added column
    file_path = Column(String(500))
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    content = Column(Text)
    extracted_text = Column(Text, nullable=True)  # Added column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submission_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String(50), default='pending')
    evaluation_status = Column(String(50), default='draft')  # draft, pending_faculty, evaluated, rejected
    extraction_method = Column(String(50), nullable=True)  # Added column
    ocr_confidence = Column(Float, nullable=True)  # Added column
    processing_metadata = Column(JSONB, nullable=True)  # Added column
    evaluation_score = Column(Float)  # Stores final marks (0-24)
    rejection_reason = Column(Text)  # Stores faculty feedback for rejected submissions
    rejection_date = Column(DateTime(timezone=True))  # When the submission was rejected
    faculty_feedback = Column(Text)  # General faculty feedback (for both rejected and evaluated)
    swot_analysis = Column(JSONB)
    error_message = Column(Text)

    # Course and Assignment relationships
    course = relationship("Course", backref="submissions")
    assignment = relationship("GeneratedAssignment", backref="submissions")
    
    # Evaluation relationships - each submission can have multiple evaluations
    faculty_evaluations = relationship(
        "FacultyEvaluationResult",
        back_populates="submission",
        cascade="all, delete-orphan"
    )
    swot_analyses = relationship(
        "StudentSWOTResult",
        back_populates="submission",
        cascade="all, delete-orphan"
    )
    evaluation_results = relationship(
        "EvaluationResult",
        back_populates="submission",
        cascade="all, delete-orphan"
    )


class FacultyEvaluationResult(Base):
    """Faculty Evaluation Result model for rubric-based evaluations"""
    __tablename__ = "faculty_evaluation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    faculty_id = Column(String(255),nullable=True)
    rubric_scores = Column(JSONB, nullable=False)
    comments = Column(Text)
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("StudentSubmission", back_populates="faculty_evaluations")

class StudentSWOTResult(Base):
    """Student SWOT Analysis Result model"""
    __tablename__ = "student_swot_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    strengths = Column(ARRAY(String), nullable=False)
    weaknesses = Column(ARRAY(String), nullable=False)
    opportunities = Column(ARRAY(String), nullable=False)
    threats = Column(ARRAY(String), nullable=False)
    suggestions = Column(ARRAY(String), nullable=False)
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("StudentSubmission", back_populates="swot_analyses")

class EvaluationResult(Base):
    """Evaluation result model for AI-based automatic evaluations"""
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship(
        "StudentSubmission",
        back_populates="evaluation_results",
        uselist=False
    )
    assignment = relationship("GeneratedAssignment")
    rubric = relationship("AssignmentRubric")
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

class StudentQuestionSet(Base):
    """Stores generated questions per student context and approval status"""
    __tablename__ = "student_question_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"))
    student_id = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    service_category = Column(String(255))
    department = Column(String(255))
    contextual_inputs = Column(JSONB)
    generated_questions = Column(ARRAY(Text), nullable=False)
    selected_question = Column(Text)
    approval_status = Column(String(50), default='pending')
    approved_by = Column(String(255))
    faculty_remarks = Column(Text)
    # ADD THIS FIELD - CRITICAL
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("generated_assignments.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="student_question_sets")
    assignment = relationship("GeneratedAssignment", back_populates="student_question_sets")

    __table_args__ = (
        CheckConstraint("approval_status IN ('pending','approved','rejected')", name='check_approval_status'),
    )

class SWOTSubmission(Base):
    """Independent table for storing SWOT analysis submissions"""
    __tablename__ = "swot_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(255), nullable=False)
    submission_id = Column(UUID(as_uuid=True), nullable=True)  # optional link to other tables
    content = Column(Text, nullable=False)
    swot_analysis = Column(JSONB, nullable=True)
    processing_status = Column(String(50), default="pending")
    evaluation_status = Column(String(50), default="draft")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


from sqlalchemy.orm import configure_mappers
configure_mappers()

