"""
Upload router for handling past assignment uploads
"""

import os
import tempfile
import shutil
import uuid
import io
import fitz
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from database.connection import get_async_db, AsyncSessionLocal
from database.repository import CourseRepository, PastAssignmentRepository, AssignmentQuestionRepository
from services.storage_service import StorageService
from services.document_processor import document_processor
from services.image_analyzer import extract_from_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/past-assignments")
async def upload_past_assignments(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    course_title: str = Form(..., description="Course title/name"),
    course_code: str = Form(..., description="Course code"),
    academic_year: str = Form(..., description="Academic year (e.g., 2023-2024)"),
    semester: int = Form(..., description="Semester number (1 or 2)"),
    files: List[UploadFile] = File(..., description="Assignment files (PDF/DOCX, max 10)")
):
    """
    Upload past assignments to build reference corpus
    """
    try:
        # Validate inputs
        if not course_title.strip():
            raise HTTPException(status_code=400, detail="Course title is required")
        
        if not course_code.strip():
            raise HTTPException(status_code=400, detail="Course code is required")
        
        if not academic_year.strip():
            raise HTTPException(status_code=400, detail="Academic year is required")
        
        if semester not in [1, 2]:
            raise HTTPException(status_code=400, detail="Semester must be 1 or 2")
        
        if not files:
            raise HTTPException(status_code=400, detail="At least one file is required")
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
        
        # Validate file types
        for file in files:
            file_ext = file.filename.lower()
            if not (file_ext.endswith('.pdf') or file_ext.endswith('.docx')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} must be PDF or DOCX format"
                )
        
        logger.info(f"Received upload request:")
        logger.info(f"  Course: {course_title} ({course_code})")
        logger.info(f"  Academic Year: {academic_year}, Semester: {semester}")
        logger.info(f"  Files: {len(files)}")
        
        # Create temporary directory in project
        try:
            # Create temp directory in project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            project_temp_dir = os.path.join(project_root, "temp")
            os.makedirs(project_temp_dir, exist_ok=True)
            
            # Create unique temp directory for this upload
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_dir = os.path.join(project_temp_dir, f"upload_{timestamp}")
            os.makedirs(temp_dir)
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Validate the directory was created and is accessible
            if not os.path.exists(temp_dir):
                raise Exception(f"Temporary directory was not created: {temp_dir}")
            if not os.path.isdir(temp_dir):
                raise Exception(f"Temporary path is not a directory: {temp_dir}")
            if not os.access(temp_dir, os.W_OK):
                raise Exception(f"Temporary directory is not writable: {temp_dir}")
                
        except Exception as e:
            logger.error(f"Failed to create temporary directory: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create temporary directory: {str(e)}")
        
        try:
            # Save uploaded files and handle DOCX conversion
            file_mappings = []
            
            for file in files:
                temp_file_path = os.path.join(temp_dir, file.filename)
                
                # Save uploaded file
                with open(temp_file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                logger.info(f"Saved uploaded file: {file.filename}")
                
                # Handle DOCX conversion
                if file.filename.lower().endswith('.docx'):
                    try:
                        logger.info(f"Converting DOCX to PDF: {file.filename}")
                        pdf_path = document_processor.convert_docx_to_pdf(temp_file_path, temp_dir)
                        
                        storage_filename = file.filename.replace('.docx', '.pdf').replace('.DOCX', '.pdf')
                        file_mappings.append({
                            'original_filename': file.filename,
                            'storage_filename': storage_filename,
                            'file_path': pdf_path,
                            'file_size': os.path.getsize(pdf_path)
                        })
                        
                        # Remove original DOCX
                        os.remove(temp_file_path)
                        
                    except Exception as e:
                        logger.error(f"Failed to convert DOCX: {file.filename} - {e}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to convert DOCX file {file.filename}: {str(e)}"
                        )
                else:
                    # PDF file - use as is
                    file_mappings.append({
                        'original_filename': file.filename,
                        'storage_filename': file.filename,
                        'file_path': temp_file_path,
                        'file_size': os.path.getsize(temp_file_path)
                    })
            
            # Initialize storage service and store files
            storage_service = StorageService(db)
            assignments = []
            
            for mapping in file_mappings:
                # Store assignment in MinIO and create database record
                assignment = await storage_service.store_past_assignment(
                    course_title=course_title,
                    course_code=course_code,
                    academic_year=academic_year,
                    semester=semester,
                    file_path=mapping['file_path'],
                    original_filename=mapping['storage_filename']
                )
                
                assignments.append(assignment)
                logger.info(f"Stored assignment: {assignment.id}")
            
            # Process files in background
            background_tasks.add_task(
                process_assignments_background,
                [mapping['file_path'] for mapping in file_mappings],
                assignments,
                temp_dir
            )
            
            return {
                "message": "Files uploaded successfully. Processing started in background.",
                "course_title": course_title,
                "course_code": course_code,
                "academic_year": academic_year,
                "semester": semester,
                "uploaded_files": [mapping['storage_filename'] for mapping in file_mappings],
                "assignment_ids": [str(assignment.id) for assignment in assignments],
                "processing_status": "processing",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Clean up temp directory on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
            
    except Exception as e:
        logger.error(f"Error in upload_past_assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_assignments_background(
    pdf_paths: List[str],
    assignments: List,
    temp_dir: str
):
    """Background task to process assignments and extract questions"""
    try:
        logger.info(f"Starting background processing for {len(pdf_paths)} assignments")
        
        # Process each PDF file
        for i, pdf_path in enumerate(pdf_paths):
            try:
                assignment = assignments[i]
                filename = os.path.basename(pdf_path)
                
                logger.info(f"Processing {filename} for assignment {assignment.id}")
                
                # Update status to processing
                async with AsyncSessionLocal() as db:
                    assignment_repo = PastAssignmentRepository(db)
                    await assignment_repo.update_status(assignment.id, "processing")
                
                # Create temporary directory for processing - EXACTLY like Question_Review_System
                with tempfile.TemporaryDirectory() as process_temp_dir:
                    logger.info(f"Created temporary directory: {process_temp_dir}")
                    logger.info(f"Temporary directory path length: {len(process_temp_dir)} characters")
                    
                    # Process the PDF using the document processor - EXACTLY like Question_Review_System
                    matches, output_files, metadata = document_processor.extract_questions_from_pdf(
                        pdf_path,
                        output_dir=process_temp_dir  # Use the temporary directory directly
                    )
                    
                    if output_files:
                        # Prepare question files for storage - EXACTLY like Question_Review_System
                        question_files_data = []
                        for j, output_file in enumerate(output_files):
                            question_number = j + 1
                            
                            # Extract text and analyze images from the question PDF
                            try:
                                # Use the image analyzer to extract text and analyze images
                                extracted_content = extract_from_pdf(output_file, output_dir=process_temp_dir)
                                if not extracted_content:
                                    # Fallback to simple text extraction if image analysis fails
                                    with fitz.open(output_file) as question_doc:
                                        extracted_content = ""
                                        for page in question_doc:
                                            extracted_content += page.get_text()
                            except ValueError as e:
                                # Handle missing environment variables for image analysis
                                logger.warning(f"Image analysis not available (missing env vars): {e}")
                                logger.info("Falling back to text-only extraction")
                                # Fallback to simple text extraction
                                with fitz.open(output_file) as question_doc:
                                    extracted_content = ""
                                    for page in question_doc:
                                        extracted_content += page.get_text()
                            except Exception as e:
                                logger.warning(f"Could not extract text from question {j+1}: {e}")
                                extracted_content = ""
                            
                            question_files_data.append({
                                'file_path': output_file,
                                'question_number': question_number,
                                'extracted_content': extracted_content,
                                'has_images': True,
                                'processing_metadata': metadata
                            })
                        
                        logger.info(f"Attempting to store {len(question_files_data)} questions in MinIO and database")
                        # Store questions in MinIO and database - EXACTLY like Question_Review_System
                        async with AsyncSessionLocal() as db:
                            storage_service = StorageService(db)
                            questions = await storage_service.store_partitioned_questions(
                                assignment.id,
                                question_files_data
                            )
                            logger.info(f"Successfully stored {len(questions)} questions")
                            
                            # Update assignment status to completed
                            assignment_repo = PastAssignmentRepository(db)
                            await assignment_repo.update_status(assignment.id, "completed")
                            
                            logger.info(f"Successfully processed {filename}: {len(questions)} questions created")
                        
                    else:
                        # Update status to failed
                        async with AsyncSessionLocal() as db:
                            assignment_repo = PastAssignmentRepository(db)
                            await assignment_repo.update_status(assignment.id, "failed")
                        logger.error(f"No questions extracted from {filename}")
                        
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {str(e)}")
                # Update status to failed
                if i < len(assignments):
                    async with AsyncSessionLocal() as db:
                        assignment_repo = PastAssignmentRepository(db)
                        await assignment_repo.update_status(assignments[i].id, "failed")
                continue
        
        logger.info("Background processing completed")
        
    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")
    
    finally:
        # Clean up temporary directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {str(e)}")

@router.get("/assignments")
async def list_past_assignments(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    course_id: Optional[str] = None
):
    """List past assignments with optional filtering"""
    try:
        assignment_repo = PastAssignmentRepository(db)
        course_uuid = uuid.UUID(course_id) if course_id else None
        
        assignments = await assignment_repo.get_all(
            skip=skip,
            limit=limit,
            course_id=course_uuid
        )
        
        assignment_list = []
        for assignment in assignments:
            assignment_data = {
                "id": str(assignment.id),
                "course_id": str(assignment.course_id),
                "course_title": assignment.course.title,
                "course_code": assignment.course.course_code,
                "academic_year": assignment.course.academic_year,
                "semester": assignment.course.semester,
                "original_file_name": assignment.original_file_name,
                "file_type": assignment.file_type,
                "file_size_mb": round(assignment.file_size / (1024 * 1024), 2) if assignment.file_size else 0,
                "processing_status": assignment.processing_status,
                "created_at": assignment.created_at.isoformat(),
                "question_count": len(assignment.questions) if assignment.questions else 0
            }
            assignment_list.append(assignment_data)
        
        return {"assignments": assignment_list, "total": len(assignment_list)}
        
    except Exception as e:
        logger.error(f"Error listing assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/assignments/{assignment_id}")
async def get_assignment_details(
    assignment_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get assignment details with questions"""
    try:
        assignment_repo = PastAssignmentRepository(db)
        assignment = await assignment_repo.get_by_id(uuid.UUID(assignment_id))
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        assignment_data = {
            "id": str(assignment.id),
            "course": {
                "id": str(assignment.course.id),
                "title": assignment.course.title,
                "code": assignment.course.course_code,
                "academic_year": assignment.course.academic_year,
                "semester": assignment.course.semester
            },
            "original_file_name": assignment.original_file_name,
            "file_type": assignment.file_type,
            "file_size_mb": round(assignment.file_size / (1024 * 1024), 2) if assignment.file_size else 0,
            "processing_status": assignment.processing_status,
            "error_message": assignment.error_message,
            "created_at": assignment.created_at.isoformat(),
            "questions": []
        }
        
        # Add question details
        for question in assignment.questions:
            question_data = {
                "id": str(question.id),
                "question_number": question.question_number,
                "extracted_content": question.extracted_content,
                "has_images": question.has_images,
                "processing_metadata": question.processing_metadata,
                "created_at": question.created_at.isoformat()
            }
            assignment_data["questions"].append(question_data)
        
        return assignment_data
        
    except Exception as e:
        logger.error(f"Error getting assignment details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status/{assignment_id}")
async def get_upload_status(
    assignment_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get assignment processing status"""
    try:
        assignment_repo = PastAssignmentRepository(db)
        assignment = await assignment_repo.get_by_id(uuid.UUID(assignment_id))
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return {
            "assignment_id": assignment_id,
            "status": assignment.processing_status,
            "error_message": assignment.error_message,
            "question_count": len(assignment.questions) if assignment.questions else 0,
            "created_at": assignment.created_at.isoformat(),
            "updated_at": assignment.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

