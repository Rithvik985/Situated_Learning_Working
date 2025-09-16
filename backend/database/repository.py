"""
Repository classes for database operations
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload, Session
from .connection import SessionLocal
from .models import Course, PastAssignment, AssignmentQuestion

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CourseRepository:
    """Repository for course operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, title: str, course_code: str, academic_year: str, semester: int, description: str = None) -> Course:
        """Create a new course"""
        course = Course(
            title=title,
            course_code=course_code,
            academic_year=academic_year,
            semester=semester,
            description=description
        )
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course
    
    async def get_or_create(self, title: str, course_code: str, academic_year: str, semester: int, description: str = None) -> Course:
        """Get existing course or create new one"""
        # Try to find existing course
        result = await self.db.execute(
            select(Course).where(
                and_(
                    Course.title == title,
                    Course.course_code == course_code,
                    Course.academic_year == academic_year,
                    Course.semester == semester
                )
            )
        )
        course = result.scalar_one_or_none()
        
        if course:
            return course
        
        # Create new course if not found
        return await self.create(title, course_code, academic_year, semester, description)
    
    async def get_by_id(self, course_id: uuid.UUID) -> Optional[Course]:
        """Get course by ID"""
        result = await self.db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get all courses with pagination"""
        result = await self.db.execute(
            select(Course)
            .offset(skip)
            .limit(limit)
            .order_by(Course.created_at.desc())
        )
        return result.scalars().all()

class PastAssignmentRepository:
    """Repository for past assignment operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, course_id: uuid.UUID, original_file_name: str, 
                    original_file_path: str, file_type: str, file_size: int) -> PastAssignment:
        """Create a new past assignment record"""
        assignment = PastAssignment(
            course_id=course_id,
            original_file_name=original_file_name,
            original_file_path=original_file_path,
            file_type=file_type,
            file_size=file_size,
            processing_status='pending'
        )
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment
    
    async def get_by_id(self, assignment_id: uuid.UUID) -> Optional[PastAssignment]:
        """Get assignment by ID with related data"""
        result = await self.db.execute(
            select(PastAssignment)
            .options(selectinload(PastAssignment.course), selectinload(PastAssignment.questions))
            .where(PastAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()
    
    async def update_status(self, assignment_id: uuid.UUID, status: str, error_message: str = None):
        """Update assignment processing status"""
        await self.db.execute(
            update(PastAssignment)
            .where(PastAssignment.id == assignment_id)
            .values(processing_status=status, error_message=error_message)
        )
        await self.db.commit()
    
    async def get_all(self, skip: int = 0, limit: int = 100, course_id: uuid.UUID = None) -> List[PastAssignment]:
        """Get all assignments with optional filtering"""
        query = select(PastAssignment).options(selectinload(PastAssignment.course))
        
        if course_id:
            query = query.where(PastAssignment.course_id == course_id)
        
        query = query.offset(skip).limit(limit).order_by(PastAssignment.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

class AssignmentQuestionRepository:
    """Repository for assignment question operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, assignment_id: uuid.UUID, question_number: int, 
                    question_text: str = None, extracted_content: str = None,
                    partitioned_file_path: str = None, has_images: bool = False,
                    processing_metadata: Dict[str, Any] = None) -> AssignmentQuestion:
        """Create a new assignment question record"""
        question = AssignmentQuestion(
            assignment_id=assignment_id,
            question_number=question_number,
            question_text=question_text,
            extracted_content=extracted_content,
            partitioned_file_path=partitioned_file_path,
            has_images=has_images,
            processing_metadata=processing_metadata or {}
        )
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question
    
    async def get_by_assignment_id(self, assignment_id: uuid.UUID) -> List[AssignmentQuestion]:
        """Get all questions for an assignment"""
        result = await self.db.execute(
            select(AssignmentQuestion)
            .where(AssignmentQuestion.assignment_id == assignment_id)
            .order_by(AssignmentQuestion.question_number)
        )
        return result.scalars().all()
    
    async def get_by_id(self, question_id: uuid.UUID) -> Optional[AssignmentQuestion]:
        """Get question by ID"""
        result = await self.db.execute(select(AssignmentQuestion).where(AssignmentQuestion.id == question_id))
        return result.scalar_one_or_none()
