"""
Storage service for handling file operations with MinIO and database
"""
import os
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from storage.minio_client import minio_client
from database.repository import CourseRepository, PastAssignmentRepository, AssignmentQuestionRepository
from database.models import PastAssignment, AssignmentQuestion
from sqlalchemy import update
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.minio_client = minio_client
        self.course_repo = CourseRepository(db)
        self.assignment_repo = PastAssignmentRepository(db)
        self.question_repo = AssignmentQuestionRepository(db)
    
    def _generate_minio_path(self, course_title: str, course_code: str, academic_year: str, 
                           semester: int, file_type: str, filename: str) -> str:
        """
        Generate MinIO object path following the structure:
        original/{course_code}/{academic_year}/semester_{semester}/{assignment_id}_{filename}
        partitioned/{course_code}/{academic_year}/semester_{semester}/{assignment_id}/question_{number}.pdf
        """
        # Clean course code and title for path
        clean_course_code = course_code.replace(" ", "_").replace("/", "_")
        
        if file_type == "original":
            return f"original/{clean_course_code}/{academic_year}/semester_{semester}/{filename}"
        elif file_type == "partitioned":
            return f"partitioned/{clean_course_code}/{academic_year}/semester_{semester}"
        else:
            return f"{file_type}/{clean_course_code}/{academic_year}/semester_{semester}/{filename}"
    
    async def store_past_assignment(self, course_title: str, course_code: str, 
                                  academic_year: str, semester: int, 
                                  file_path: str, original_filename: str) -> PastAssignment:
        """
        Store a past assignment file in MinIO and create database record
        
        Args:
            course_title: Course title
            course_code: Course code
            academic_year: Academic year
            semester: Semester number
            file_path: Local path to the file
            original_filename: Original filename
            
        Returns:
            PastAssignment: Created assignment record
        """
        try:
            # Get or create course
            course = await self.course_repo.get_or_create(
                title=course_title,
                course_code=course_code,
                academic_year=academic_year,
                semester=semester
            )
            
            # Generate file info
            file_size = os.path.getsize(file_path)
            file_type = "pdf" if original_filename.lower().endswith('.pdf') else "docx"
            
            # Create assignment record first to get ID for MinIO path
            assignment = await self.assignment_repo.create(
                course_id=course.id,
                original_file_name=original_filename,
                original_file_path="",  # Will be updated after MinIO upload
                file_type=file_type,
                file_size=file_size
            )
            
            # Generate MinIO path with assignment ID
            assignment_filename = f"{assignment.id}_{original_filename}"
            minio_path = self._generate_minio_path(
                course_title, course_code, academic_year, semester, 
                "original", assignment_filename
            )
            
            # Upload to MinIO
            self.minio_client.upload_file(file_path, minio_path)
            
            # Update assignment record with MinIO path
            await self.db.execute(
                update(PastAssignment)
                .where(PastAssignment.id == assignment.id)
                .values(original_file_path=minio_path)
            )
            await self.db.commit()
            
            logger.info(f"✅ Stored past assignment: {original_filename} -> {minio_path}")
            return assignment
            
        except Exception as e:
            logger.error(f"❌ Error storing past assignment: {e}")
            await self.db.rollback()
            raise
    
    async def store_partitioned_questions(self, assignment_id: uuid.UUID, 
                                        question_files: List[Dict[str, Any]]) -> List[AssignmentQuestion]:
        """
        Store partitioned question files in MinIO and create database records
        
        Args:
            assignment_id: Assignment ID
            question_files: List of question file info dicts
            
        Returns:
            List[AssignmentQuestion]: Created question records
        """
        try:
            # Get assignment details for MinIO path generation
            assignment = await self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                raise ValueError(f"Assignment not found: {assignment_id}")
            
            course = assignment.course
            
            questions = []
            base_path = self._generate_minio_path(
                course.title, course.course_code, course.academic_year, 
                course.semester, "partitioned", ""
            )
            
            for question_file in question_files:
                file_path = question_file['file_path']
                question_number = question_file['question_number']
                extracted_content = question_file.get('extracted_content', '')
                has_images = question_file.get('has_images', False)
                processing_metadata = question_file.get('processing_metadata', {})
                
                # Generate MinIO path for partitioned question
                question_filename = f"question_{question_number:02d}.pdf"
                minio_path = f"{base_path}/{assignment_id}/{question_filename}"
                
                # Upload to MinIO
                self.minio_client.upload_file(file_path, minio_path)
                
                # Create question record
                question = await self.question_repo.create(
                    assignment_id=assignment_id,
                    question_number=question_number,
                    extracted_content=extracted_content,
                    partitioned_file_path=minio_path,
                    has_images=has_images,
                    processing_metadata=processing_metadata
                )
                
                questions.append(question)
                logger.info(f"✅ Stored question {question_number}: {minio_path}")
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error storing partitioned questions: {e}")
            await self.db.rollback()
            raise
    
    async def get_assignment_file(self, assignment_id: uuid.UUID) -> Optional[bytes]:
        """Get original assignment file from MinIO"""
        try:
            assignment = await self.assignment_repo.get_by_id(assignment_id)
            if not assignment or not assignment.original_file_path:
                return None
            
            return self.minio_client.get_file_object(assignment.original_file_path)
        except Exception as e:
            logger.error(f"❌ Error getting assignment file: {e}")
            return None
    
    async def get_question_file(self, question_id: uuid.UUID) -> Optional[bytes]:
        """Get partitioned question file from MinIO"""
        try:
            question = await self.question_repo.get_by_id(question_id)
            if not question or not question.partitioned_file_path:
                return None
            
            return self.minio_client.get_file_object(question.partitioned_file_path)
        except Exception as e:
            logger.error(f"❌ Error getting question file: {e}")
            return None
