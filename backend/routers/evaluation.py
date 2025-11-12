"""
Evaluation router for student submission assessment
Following the requirements:
1. Course selection (only courses with saved assignments)
2. Assignment selection (single assignment)
3. Rubric selection/generation
4. Student submission upload and processing
5. Evaluation and scoring
6. Faculty review and adjustments
7. Report generation
"""

import uuid
import logging
import os
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from database.models import (
    GeneratedAssignment as DBGeneratedAssignment,
    AssignmentRubric as DBAssignmentRubric,
    StudentSubmission as DBStudentSubmission,
    FacultyEvaluationResult as DBFacultyEvaluation,
    StudentSWOTResult as DBStudentSWOT,
    EvaluationResult as DBEvaluationResult,
    Course as DBCourse
)
from database.repository import get_db
from services.rubric_parser import fetch_rubric
from services.submission_processor import SubmissionProcessingService
from storage.minio_client import minio_client

# Configure logging
logger = logging.getLogger('evaluation_server.router')
logger.setLevel(logging.DEBUG)

# Control whether to log full extracted content. Set env var SHOW_FULL_EXTRACTED_LOGS=true to enable.
SHOW_FULL_EXTRACTED_LOGS = os.getenv("SHOW_FULL_EXTRACTED_LOGS", "false").lower() in ("1", "true", "yes")

router = APIRouter()

# Initialize submission processing service
submission_processor = SubmissionProcessingService()

# Pydantic models for SWOT analysis
class SWOTAnalysis(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    suggestions: List[str]

class SWOTRequest(BaseModel):
    student_id: str
    submission_id: str
    content: str

class FacultyEvaluation(BaseModel):
    submission_id: str
    rubric_scores: Dict[str, float]
    comments: Optional[str] = None

class SubmissionSummary(BaseModel):
    submission_id: str
    student_id: str
    student_name: str
    submission_date: datetime
    content: str

@router.post("/student/swot", response_model=SWOTAnalysis)
async def create_swot_analysis(request: SWOTRequest, db: Session = Depends(get_db)):
    """
    Create a SWOT analysis for a student submission
    """
    try:
        # Validate submission exists
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == request.submission_id,
            DBStudentSubmission.student_id == request.student_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Generate SWOT analysis using the submission processor
        swot_analysis = submission_processor.generate_swot_analysis(request.content)
        
        # Create SWOT analysis result
        swot_result = DBStudentSWOT(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            strengths=swot_analysis.strengths,
            weaknesses=swot_analysis.weaknesses,
            opportunities=swot_analysis.opportunities,
            threats=swot_analysis.threats,
            suggestions=swot_analysis.suggestions
        )
        
        # Add and commit the SWOT analysis
        db.add(swot_result)
        db.commit()
        
        return swot_analysis
        
    except Exception as e:
        logger.error(f"Error creating SWOT analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating SWOT analysis")

@router.get("/faculty/pending", response_model=List[SubmissionSummary])
async def get_pending_submissions(course_id: str, db: Session = Depends(get_db)):
    """
    Get all pending submissions for faculty evaluation
    """
    try:
        submissions = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.course_id == course_id,
            DBStudentSubmission.evaluation_status == "pending"
        ).all()
        
        return [SubmissionSummary(
            submission_id=sub.id,
            student_id=sub.student_id,
            student_name=sub.student_name,
            submission_date=sub.submission_date,
            content=sub.content
        ) for sub in submissions]
        
    except Exception as e:
        logger.error(f"Error fetching pending submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching pending submissions")

@router.post("/faculty/evaluate/{submission_id}")
async def evaluate_submission(
    submission_id: str,
    evaluation: FacultyEvaluation,
    db: Session = Depends(get_db)
):
    """
    Faculty evaluation of a student submission using rubric
    """
    try:
        # Get submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Create faculty evaluation result
        faculty_evaluation = DBFacultyEvaluation(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            rubric_scores=evaluation.rubric_scores,
            comments=evaluation.comments,
            evaluation_date=datetime.utcnow()
        )
        
        # Update submission status
        submission.evaluation_status = "completed"
        
        # Save to database
        db.add(faculty_evaluation)
        db.commit()
        
        return {"message": "Evaluation completed successfully"}
        
    except Exception as e:
        logger.error(f"Error evaluating submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Error evaluating submission")
    submission_text: str

class SWOTResponse(BaseModel):
    submission_id: str
    analysis: SWOTAnalysis
    iteration: int
    final: bool

# Pydantic models for rubric evaluation
class RejectionRequest(BaseModel):
    rejection_reason: str
    faculty_id: str

class RubricCriterion(BaseModel):
    name: str
    description: str
    max_score: float
    score: Optional[float] = None
    feedback: Optional[str] = None

class RubricEvaluation(BaseModel):
    submission_id: str
    criteria: List[RubricCriterion]
    total_score: float
    overall_feedback: str
    evaluated_by: str
    evaluation_date: datetime

class RubricRequest(BaseModel):
    faculty_id: str
    submission_id: str
    criteria_scores: Dict[str, float]
    feedback: str

# Initialize submission processing service
submission_processor = SubmissionProcessingService()

@router.post("/student/swot", response_model=SWOTResponse)
async def analyze_student_submission(request: SWOTRequest, db: Session = Depends(get_db)):
    """
    Analyze student submission using SWOT analysis.
    Students can submit multiple times for iterative feedback.
    """
    try:
        # Get existing submission details
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == uuid.UUID(request.submission_id)
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Get iteration count
        iteration = db.query(DBEvaluationResult).filter(
            DBEvaluationResult.submission_id == uuid.UUID(request.submission_id),
            DBEvaluationResult.type == 'swot'
        ).count() + 1

        # Perform SWOT analysis using LLM
        analysis = await submission_processor.perform_swot_analysis(
            request.submission_text,
            submission.assignment.requirements if submission.assignment else []
        )
        
        # Save analysis result
        result = DBEvaluationResult(
            id=uuid.uuid4(),
            submission_id=uuid.UUID(request.submission_id),
            evaluator_id=request.student_id,
            type='swot',
            scores={},  # SWOT doesn't have numerical scores
            feedback=analysis.dict(),
            iteration=iteration
        )
        db.add(result)
        db.commit()
        
        return SWOTResponse(
            submission_id=request.submission_id,
            analysis=analysis,
            iteration=iteration,
            final=iteration >= 3  # Limit to 3 iterations
        )
        
    except Exception as e:
        logger.error(f"Error in SWOT analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/faculty/evaluate", response_model=RubricEvaluation)
async def faculty_evaluation(request: RubricRequest, db: Session = Depends(get_db)):
    """
    Faculty performs final rubric-based evaluation of student submission
    """
    try:
        # Get submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == uuid.UUID(request.submission_id)
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Calculate total score
        total_score = sum(request.criteria_scores.values())
        
        # Create evaluation result
        result = DBEvaluationResult(
            id=uuid.uuid4(),
            submission_id=uuid.UUID(request.submission_id),
            evaluator_id=request.faculty_id,
            type='rubric',
            scores=request.criteria_scores,
            feedback=request.feedback,
            total_score=total_score
        )
        db.add(result)
        
        # Update submission status
        submission.evaluation_status = 'completed'
        db.commit()
        
        return RubricEvaluation(
            submission_id=request.submission_id,
            criteria=[
                RubricCriterion(
                    name=name,
                    description=submission.assignment.rubric.get(name, {}).get('description', ''),
                    max_score=submission.assignment.rubric.get(name, {}).get('max_score', 10),
                    score=score,
                    feedback=submission.assignment.rubric.get(name, {}).get('feedback', '')
                )
                for name, score in request.criteria_scores.items()
            ],
            total_score=total_score,
            overall_feedback=request.feedback,
            evaluated_by=request.faculty_id,
            evaluation_date=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in faculty evaluation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Helper to transform hardcoded MySQL rubric dimensions into app's expected structure
def _transform_mysql_rubric_to_app_structure(dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert dimensions list (from MySQL) into {'rubrics': [{category, questions}...]}
    so the evaluation service can consume it uniformly.
    """
    rubrics: List[Dict[str, Any]] = []
    for dim in dimensions or []:
        category_name = dim.get('name', 'Unnamed Category')
        criteria_output = dim.get('criteria_output', {}) or {}
        questions: List[str] = []
        for crit_key, crit_desc in criteria_output.items():
            # Form a clear evaluation prompt segment for each sub-criterion
            questions.append(f"{category_name} > {crit_key}: {crit_desc}")
        if questions:
            rubrics.append({
                'category': category_name,
                'questions': questions
            })
    return {'rubrics': rubrics}

# Response Models
class CourseResponse(BaseModel):
    id: str
    title: str
    course_code: str
    academic_year: str
    semester: int
    saved_assignment_count: int
    
    class Config:
        from_attributes = True

class SavedAssignmentResponse(BaseModel):
    id: str
    assignment_name: str
    title: str
    description: str
    difficulty_level: str
    topics: List[str]
    domains: List[str]
    created_at: datetime
    has_rubric: bool
    
    class Config:
        from_attributes = True

class RubricResponse(BaseModel):
    id: str
    rubric_name: str
    doc_type: str
    criteria: Dict[str, Any]
    is_edited: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubmissionResponse(BaseModel):
    id: str
    file_name: str
    file_path: str
    extracted_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_status: str
    extraction_method: Optional[str] = None
    
    class Config:
        from_attributes = True

class CriterionResult(BaseModel):
    category: str
    score: float
    max_score: float
    percentage: float
    feedback: str

class EvaluationResult(BaseModel):
    submission_id: str
    overall_score: float  # Out of 20
    criterion_results: List[CriterionResult]
    overall_feedback: str
    plagiarism_score: Optional[float] = None
    ai_detection_score: Optional[float] = None
    flags: List[str] = []
    faculty_reviewed: bool = False
    faculty_adjustments: Optional[Dict[str, Any]] = None
    faculty_feedback: Optional[str] = None

# Request Models
class CourseSelectionRequest(BaseModel):
    course_id: str
    academic_year: str
    semester: int

class EvaluationRequest(BaseModel):
    submission_id: str
    criteria_scores: Dict[str, float]
    feedback: str
    faculty_id: Optional[str]='f20220162'

class FacultyReviewRequest(BaseModel):
    adjusted_scores: Dict[str, Any]
    faculty_feedback: str
    reason_for_adjustment: str

# Step 1: Course Selection API
@router.get("/courses", response_model=List[CourseResponse])
async def get_courses_with_saved_assignments(db: Session = Depends(get_db)):
    """
    Get list of unique course titles that have saved assignments for evaluation
    Returns unique course titles with their available academic years and semesters
    """
    try:
        # Query courses that have saved assignments - get unique titles
        courses_with_assignments = db.query(DBCourse.title).join(
            DBGeneratedAssignment, DBCourse.id == DBGeneratedAssignment.course_id
        ).filter(
            DBGeneratedAssignment.is_selected == True,
            DBGeneratedAssignment.assignment_name.isnot(None)
        ).distinct().all()
        
        course_responses = []
        for course_tuple in courses_with_assignments:
            course_title = course_tuple[0]
            
            # Get all courses with this title to find available academic years and semesters
            courses_with_title = db.query(DBCourse).filter(
                DBCourse.title == course_title
            ).all()
            
            # Count total saved assignments for this course title
            assignment_count = db.query(DBGeneratedAssignment).join(
                DBCourse, DBCourse.id == DBGeneratedAssignment.course_id
            ).filter(
                DBCourse.title == course_title,
                DBGeneratedAssignment.is_selected == True,
                DBGeneratedAssignment.assignment_name.isnot(None)
            ).count()
            
            # Use the first course entry for basic info, but this represents all courses with this title
            first_course = courses_with_title[0]
            
            course_responses.append(CourseResponse(
                id=str(first_course.id),  # This will be used for filtering, but we'll filter by title
                title=course_title,
                course_code=first_course.course_code,
                academic_year=first_course.academic_year,
                semester=first_course.semester,
                saved_assignment_count=assignment_count
            ))
        
        return course_responses
        
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")

@router.get("/courses/{course_title}/filters")
async def get_course_filters(course_title: str, db: Session = Depends(get_db)):
    """
    Get available academic years and semesters for a specific course title
    """
    try:
        # Get all courses with this title that have saved assignments
        courses = db.query(DBCourse).join(
            DBGeneratedAssignment, DBCourse.id == DBGeneratedAssignment.course_id
        ).filter(
            DBCourse.title == course_title,
            DBGeneratedAssignment.is_selected == True,
            DBGeneratedAssignment.assignment_name.isnot(None)
        ).distinct().all()
        
        # Extract unique academic years and semesters
        academic_years = list(set([course.academic_year for course in courses if course.academic_year]))
        semesters = list(set([course.semester for course in courses if course.semester]))
        
        return {
            "academic_years": sorted(academic_years),
            "semesters": sorted(semesters)
        }
        
    except Exception as e:
        logger.error(f"Error fetching course filters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch course filters: {str(e)}")

# Step 2: Assignment Selection API  
@router.get("/courses/{course_title}/assignments", response_model=List[SavedAssignmentResponse])
async def get_saved_assignments_for_course(
    course_title: str,
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get saved assignments for a specific course title
    Filter by academic year and semester if provided
    """
    try:
        # Build query for saved assignments - join with course table for filtering
        query = db.query(DBGeneratedAssignment).join(
            DBCourse, DBCourse.id == DBGeneratedAssignment.course_id
        ).filter(
            DBCourse.title == course_title,
            DBGeneratedAssignment.is_selected == True,
            DBGeneratedAssignment.assignment_name.isnot(None)
        )
        
        # Apply additional filters if provided
        if academic_year:
            query = query.filter(DBCourse.academic_year == academic_year)
        
        if semester:
            query = query.filter(DBCourse.semester == semester)
        
        assignments = query.all()
        
        # Convert to response models and check for rubrics
        assignment_responses = []
        for assignment in assignments:
            # Check if assignment has an associated rubric
            has_rubric = db.query(DBAssignmentRubric).filter(
                DBAssignmentRubric.assignment_ids.contains([assignment.id])
            ).first() is not None
            
            assignment_responses.append(SavedAssignmentResponse(
                id=str(assignment.id),
                assignment_name=assignment.assignment_name,
                title=assignment.title,
                description=assignment.description,
                difficulty_level=assignment.difficulty_level,
                topics=assignment.topics,
                domains=assignment.domains,
                created_at=assignment.created_at,
                has_rubric=has_rubric
            ))
        
        return assignment_responses
        
    except Exception as e:
        logger.error(f"Error fetching assignments for course {course_title}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignments: {str(e)}")

# Step 3: Rubric Selection API
@router.get("/assignments/{assignment_id}/rubrics", response_model=List[RubricResponse])
async def get_rubrics_for_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """
    Get available rubrics for a specific assignment
    """
    try:
        assignment_uuid = uuid.UUID(assignment_id)
        
        # Always ensure a rubric exists for this assignment using the hardcoded rubric
        existing = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.assignment_ids.contains([assignment_uuid])
        ).first()

        if not existing:
            # Load hardcoded rubric from MySQL and persist as the assignment's rubric
            mysql_dimensions = fetch_rubric(rubric_name="Situated_Learning_rubric", as_text=False)
            if not mysql_dimensions:
                raise HTTPException(status_code=500, detail="Hardcoded rubric not found in MySQL")
            transformed = _transform_mysql_rubric_to_app_structure(mysql_dimensions)
            new_rubric = DBAssignmentRubric(
                id=uuid.uuid4(),
                assignment_ids=[assignment_uuid],
                rubric_name="Situated_Learning_rubric",
                doc_type="Assignment",
                criteria=transformed
            )
            db.add(new_rubric)
            db.commit()
            existing = new_rubric

        return [RubricResponse(
            id=str(existing.id),
            rubric_name=existing.rubric_name,
            doc_type=existing.doc_type,
            criteria=existing.criteria,
            is_edited=existing.is_edited,
            created_at=existing.updated_at or existing.created_at
        )]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        logger.error(f"Error fetching rubrics for assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rubrics: {str(e)}")

# Step 4: Student Submission Upload API
@router.post("/submissions/upload", response_model=List[SubmissionResponse])
async def upload_student_submissions(
    assignment_id: str = Form(...),
    student_id: Optional[str] = Form(None),  # Made optional for now
    course_id: Optional[str] = Form(None),   # Made optional for now
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload student submissions for evaluation (max 5 files, PDF/DOCX only)
    Files are processed and stored in MinIO, text extracted if needed
    Only processes new files, skips already processed ones
    
    Parameters:
    - assignment_id: UUID of the assignment
    - student_id: ID of the student submitting (optional - will be pulled from assignment)
    - course_id: UUID of the course (optional - will be pulled from assignment)
    - files: List of files to upload (max 5, PDF/DOCX only)
    """
    print("UPLOAD STUDENT SUBMISSIONS CALLED")
    try:
        # Log incoming request parameters
        logger.debug("="*50)
        logger.debug("UPLOAD REQUEST RECEIVED")
        logger.debug("="*50)
        logger.info(f"REQUEST PARAMETERS:")
        logger.info(f"→ student_id: {student_id!r} (type: {type(student_id).__name__})")
        logger.info(f"→ course_id: {course_id!r} (type: {type(course_id).__name__})")
        logger.info(f"→ assignment_id: {assignment_id!r}")
        logger.info(f"→ Number of files: {len(files)}")
        logger.info(f"→ File names: {[f.filename for f in files]}")
        logger.debug("-"*50)

        # Validate file count
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 submissions allowed per evaluation")
    
        # Validate assignment exists and get course info
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Log assignment details
        logger.debug("="*50)
        logger.debug("ASSIGNMENT DETAILS")
        logger.debug("="*50)
        logger.info(f"FOUND ASSIGNMENT:")
        logger.info(f"→ Assignment ID: {assignment.id}")
        logger.info(f"→ Assignment course_id: {assignment.course_id}")
        
        # Use provided values or get from assignment
        final_student_id = student_id or "TEMP_STUDENT"  # This should be replaced with actual student ID from auth
        final_course_id = course_id or str(assignment.course_id)
        
        # Log final values
        logger.debug("="*50)
        logger.debug("FINAL VALUES")
        logger.debug("="*50)
        logger.info(f"AFTER FALLBACK:")
        logger.info(f"→ final_student_id: {final_student_id!r}")
        logger.info(f"→ final_course_id: {final_course_id!r}")
        logger.debug("-"*50)
        
        if not final_course_id:
            logger.error(f"Course ID missing - student_id: {student_id}, course_id: {course_id}, assignment.course_id: {assignment.course_id}")
            raise HTTPException(status_code=400, detail="Course ID not found - either provide it or ensure assignment has course_id")
        
        # Check for existing submissions (but don't delete them)
        existing_submissions = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.assignment_id == uuid.UUID(assignment_id)
        ).all()
        
        if existing_submissions:
            logger.info(f"Found {len(existing_submissions)} existing submissions for assignment {assignment_id}. New submissions will be added alongside existing ones.")
        
        submission_responses = []
        
        logger.info(f"Processing {len(files)} files for assignment {assignment_id}")
        
        # Process each uploaded file
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only PDF and DOCX files are allowed.")
            
            # Read file content
            file_content = await file.read()
            submission_id = str(uuid.uuid4())
            
            # Process the file to extract text
            processing_result = submission_processor.process_submission_bytes(
                file_bytes=file_content,
                filename=file.filename,
                submission_id=submission_id
            )
            
            # Determine processing status and extract text
            if processing_result["status"] == "success":
                extracted_text = processing_result["extracted_text"]
                ocr_confidence = processing_result.get("confidence", 1.0)
                extraction_method = processing_result.get("extraction_method", "standard")
                processing_status = "processed"
                # Log extracted text (full or preview) depending on environment flag
                try:
                    if extracted_text:
                        text_length = len(extracted_text)
                        if SHOW_FULL_EXTRACTED_LOGS:
                            logger.info(f"[EXTRACTED TEXT - FULL] File: {file.filename}, Submission: {submission_id}, Length: {text_length} chars")
                            logger.info(f"Content:\n{extracted_text}")
                        else:
                            preview = extracted_text[:200] + "..." if text_length > 200 else extracted_text
                            logger.info(f"[EXTRACTED TEXT] File: {file.filename}, Submission: {submission_id}, Length: {text_length} chars, Preview: {preview!r}")
                    else:
                        logger.warning(f"[EXTRACTED TEXT] File: {file.filename} extracted but text is empty or None")
                except Exception as e:
                    # Defensive: don't break upload on logging issues
                    logger.exception(f"Error while logging extracted text: {e}")
            else:
                extracted_text = None
                ocr_confidence = 0.0
                extraction_method = "failed"
                processing_status = "failed"
                logger.error(f"Processing failed for {file.filename}: {processing_result.get('error_message', 'Unknown error')}")
            
            # Generate MinIO path for student submissions
            # Following structure: student_submissions/{assignment_id}/{submission_id}_{filename}
            minio_path = f"student_submissions/{assignment_id}/{submission_id}_{file.filename}"
            
            # Store file in MinIO
            try:
                # Reset file position to beginning
                await file.seek(0)
                file_content = await file.read()
                
                # Upload to MinIO
                import io
                file_obj = io.BytesIO(file_content)
                content_type = "application/pdf" if file.filename.lower().endswith('.pdf') else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
                minio_client.upload_file_object(
                    file_obj, 
                    minio_path, 
                    len(file_content),
                    content_type
                )
                logger.info(f"Uploaded {file.filename} to MinIO: {minio_path}")
                
            except Exception as e:
                logger.error(f"Failed to upload {file.filename} to MinIO: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to store file {file.filename}")
            
            # Log submission creation details
            logger.debug("="*50)
            logger.debug("CREATING SUBMISSION")
            logger.debug("="*50)
            logger.info(f"SUBMISSION DETAILS:")
            logger.info(f"→ submission_id: {submission_id!r}")
            logger.info(f"→ student_id: {final_student_id!r}")
            logger.info(f"→ course_id: {final_course_id!r}")
            logger.info(f"→ file: {file.filename!r}")
            logger.debug("-"*50)
            
            # Create database entry with MinIO path
            submission = DBStudentSubmission(
                id=uuid.UUID(submission_id),
                student_id=final_student_id,  # Use final_student_id
                course_id=uuid.UUID(final_course_id),  # Use final_course_id
                assignment_id=uuid.UUID(assignment_id),
                original_file_name=file.filename,
                file_path=minio_path,  # Store MinIO path instead of temp path
                file_type=file.filename.split('.')[-1].lower(),
                extracted_text=extracted_text,
                ocr_confidence=ocr_confidence,
                processing_status='pending',
                evaluation_status='draft'
            )
            
            # Log the created submission object
            logger.info("Submission object created:")
            logger.info(f"ID: {submission.id}")
            logger.info(f"Student ID: {submission.student_id}")
            logger.info(f"Course ID: {submission.course_id}")
            
            db.add(submission)
            db.flush()
            
            submission_responses.append(SubmissionResponse(
                id=submission_id,
                file_name=submission.original_file_name,
                file_path=submission.file_path,
                extracted_text=extracted_text[:200] + "..." if extracted_text and len(extracted_text) > 200 else extracted_text,
                ocr_confidence=ocr_confidence,
                processing_status=processing_status,
                extraction_method=extraction_method
            ))
        
        db.commit()
        logger.info(f"Successfully processed {len(files)} new submissions")
        logger.info(f"New submission IDs: {[resp.id for resp in submission_responses]}")
        return submission_responses
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload submissions: {str(e)}")

# Get all submissions for an assignment
@router.get("/assignments/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_assignment_submissions(
    assignment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all submissions for a specific assignment
    """
    try:
        # Validate assignment exists
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Get all submissions for this assignment
        submissions = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.assignment_id == uuid.UUID(assignment_id)
        ).order_by(DBStudentSubmission.created_at.desc()).all()
        
        submission_responses = []
        for submission in submissions:
            # Optionally log stored extracted text for each submission
            try:
                if submission.extracted_text:
                    text_length = len(submission.extracted_text)
                    if SHOW_FULL_EXTRACTED_LOGS:
                        logger.info(f"[STORED TEXT - FULL] Submission: {submission.id}, Length: {text_length} chars")
                        logger.info(f"Content:\n{submission.extracted_text}")
                    else:
                        preview = submission.extracted_text[:200] + "..." if text_length > 200 else submission.extracted_text
                        logger.info(f"[STORED TEXT] Submission: {submission.id}, Length: {text_length} chars, Preview: {preview!r}")
                else:
                    logger.warning(f"[STORED TEXT] Submission: {submission.id} has no extracted text")
            except Exception as e:
                logger.exception(f"Error while logging stored extracted text for submission: {e}")

            submission_responses.append(SubmissionResponse(
                id=str(submission.id),
                file_name=submission.original_file_name,
                file_path=submission.file_path,
                extracted_text=submission.extracted_text[:200] + "..." if submission.extracted_text and len(submission.extracted_text) > 200 else submission.extracted_text,
                ocr_confidence=submission.ocr_confidence or 0.0,
                processing_status="processed" if submission.extracted_text else "failed",
                extraction_method="standard"  # Could be enhanced to track this in DB
            ))
        
        logger.info(f"Retrieved {len(submission_responses)} submissions for assignment {assignment_id}")
        return submission_responses
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        logger.error(f"Error fetching submissions for assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch submissions: {str(e)}")

# Step 5: Evaluation API
@router.post("/evaluate", response_model=List[EvaluationResult])
async def evaluate_submissions_against_rubric(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate submissions for an assignment against the selected rubric.
    If submission_ids are provided, only those specific submissions will be evaluated.
    If submission_ids is None/empty, all submissions for the assignment will be evaluated (backward compatibility).
    """
    try:
        # Validate assignment
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(request.assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Load hardcoded rubric from MySQL, materialize/ensure a local rubric row, and use it
        mysql_dimensions = fetch_rubric(rubric_name="Situated_Learning_rubric", as_text=False)
        if not mysql_dimensions:
            raise HTTPException(status_code=500, detail="Hardcoded rubric not found in MySQL")
        transformed_rubric = _transform_mysql_rubric_to_app_structure(mysql_dimensions)

        # Ensure a rubric DB record exists for FK integrity and report generation
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.assignment_ids.contains([uuid.UUID(request.assignment_id)])
        ).first()
        if not rubric:
            rubric = DBAssignmentRubric(
                id=uuid.uuid4(),
                assignment_ids=[uuid.UUID(request.assignment_id)],
                rubric_name="Situated_Learning_rubric",
                doc_type="Assignment",
                criteria=transformed_rubric
            )
            db.add(rubric)
            db.flush()
        
        # Get submissions for this assignment
        if request.submission_ids:
            # Filter to only the specified submission IDs
            submission_uuids = [uuid.UUID(sid) for sid in request.submission_ids]
            submissions = db.query(DBStudentSubmission).filter(
                DBStudentSubmission.assignment_id == uuid.UUID(request.assignment_id),
                DBStudentSubmission.id.in_(submission_uuids)
            ).all()
            
            # Verify all requested submissions exist
            found_ids = {str(sub.id) for sub in submissions}
            missing_ids = set(request.submission_ids) - found_ids
            if missing_ids:
                raise HTTPException(status_code=404, detail=f"Submissions not found: {', '.join(missing_ids)}")
                
            logger.info(f"Evaluating {len(submissions)} specific submissions: {request.submission_ids}")
        else:
            # Get all submissions for this assignment (backward compatibility)
            submissions = db.query(DBStudentSubmission).filter(
                DBStudentSubmission.assignment_id == uuid.UUID(request.assignment_id)
            ).all()
            logger.info(f"Evaluating all {len(submissions)} submissions for assignment {request.assignment_id}")
        
        if not submissions:
            if request.submission_ids:
                raise HTTPException(status_code=400, detail="None of the specified submissions were found")
            else:
                raise HTTPException(status_code=400, detail="No submissions found for this assignment")
        
        evaluation_results = []
        
        # Get assignment description for evaluation context
        assignment_description = f"{assignment.title}\n\n{assignment.description}"
        
        # Evaluate each submission using the robust evaluation service
        logger.info(f"Starting evaluation of {len(submissions)} submissions for assignment {request.assignment_id}")
        for i, submission in enumerate(submissions, 1):
            try:
                logger.info(f"Processing submission {i}/{len(submissions)}: {submission.original_file_name} (ID: {submission.id})")
                
                # Check if submission has extracted text
                if not submission.extracted_text:
                    logger.warning(f"No extracted text for submission {submission.id}, skipping evaluation")
                    continue
                # Optionally log the text that will be evaluated
                try:
                    if submission.extracted_text:
                        text_length = len(submission.extracted_text)
                        if SHOW_FULL_EXTRACTED_LOGS:
                            logger.info(f"[EVALUATION TEXT - FULL] Submission: {submission.id}, Length: {text_length} chars")
                            logger.info(f"Content:\n{submission.extracted_text}")
                        else:
                            preview = submission.extracted_text[:200] + "..." if text_length > 200 else submission.extracted_text
                            logger.info(f"[EVALUATION TEXT] Submission: {submission.id}, Length: {text_length} chars, Preview: {preview!r}")
                except Exception as e:
                    logger.exception(f"Error while logging submission text before evaluation: {e}")

                # Use submission processing service for evaluation
                evaluation_result = submission_processor.evaluate_submission(
                    submission_text=submission.extracted_text,
                    assignment_description=assignment_description,
                    rubric=transformed_rubric,
                    submission_id=str(submission.id)
                )
                
                # Prepare evaluation metadata
                evaluation_metadata = {
                    "plagiarism_score": None,  # TODO: Implement plagiarism detection
                    "ai_detection_score": None,  # TODO: Implement AI detection
                    "evaluation_engine": "llm_based_enhanced",
                    "processing_time": float(evaluation_result.processing_time),
                    "total_raw_score": evaluation_result.evaluation_metadata.get('total_raw_score', 0),
                    "total_possible_score": evaluation_result.evaluation_metadata.get('total_possible_score', 0),
                    "normalization_factor": evaluation_result.evaluation_metadata.get('normalization_factor', 0),
                    "criteria_count": evaluation_result.evaluation_metadata.get('criteria_count', 0)
                }
                
                # Prepare criterion scores for database storage
                criterion_scores = {}
                for criterion_eval in evaluation_result.criterion_evaluations:
                    criterion_scores[criterion_eval.category] = {
                        "score": float(criterion_eval.score),
                        "max_score": float(criterion_eval.max_score),
                        "percentage": float(criterion_eval.percentage),
                        "feedback": criterion_eval.feedback,
                        "question_details": [
                            {
                                "question": q.question,
                                "score": q.score,
                                "reasoning": q.reasoning
                            }
                            for q in criterion_eval.question_results
                        ]
                    }
                
                # Create database evaluation record
                evaluation = DBEvaluationResult(
                    id=uuid.uuid4(),
                    submission_id=submission.id,
                    assignment_id=uuid.UUID(request.assignment_id),
                    rubric_id=rubric.id,
                    overall_score=float(evaluation_result.overall_score),  # Out of 20
                    criterion_scores=criterion_scores,
                    ai_feedback=evaluation_result.overall_feedback,
                    evaluation_metadata=evaluation_metadata,
                    flags=[]
                )
                
                db.add(evaluation)
                db.flush()
                
                # Prepare response with criterion results
                criterion_results = []
                for criterion_eval in evaluation_result.criterion_evaluations:
                    criterion_results.append(CriterionResult(
                        category=criterion_eval.category,
                        score=criterion_eval.score,
                        max_score=criterion_eval.max_score,
                        percentage=criterion_eval.percentage,
                        feedback=criterion_eval.feedback
                    ))
                
                evaluation_results.append(EvaluationResult(
                    submission_id=str(submission.id),
                    overall_score=float(evaluation_result.overall_score),  # Out of 20
                    criterion_results=criterion_results,
                    overall_feedback=evaluation_result.overall_feedback,
                    plagiarism_score=evaluation_metadata.get("plagiarism_score"),
                    ai_detection_score=evaluation_metadata.get("ai_detection_score"),
                    flags=[],
                    faculty_reviewed=False
                ))
                
                logger.info(f"Successfully evaluated submission {submission.id}: {evaluation_result.overall_score}/20 ({(evaluation_result.overall_score/20)*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error evaluating submission {submission.id}: {str(e)}")
                # Create a failed evaluation record
                evaluation_results.append(EvaluationResult(
                    submission_id=str(submission.id),
                    overall_score=0.0,
                    criterion_results=[],
                    overall_feedback=f"Evaluation failed: {str(e)}",
                    plagiarism_score=None,
                    ai_detection_score=None,
                    flags=["evaluation_failed"],
                    faculty_reviewed=False
                ))
        
        db.commit()
        return evaluation_results
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error evaluating submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate submissions: {str(e)}")

# Step 6: Faculty Review API
@router.put("/submissions/{submission_id}/review")
async def faculty_review_submission(
    submission_id: str,
    request: FacultyReviewRequest,
    db: Session = Depends(get_db)
):
    """Faculty review and adjustment of AI evaluation"""
    try:
        # Find the evaluation result
        evaluation = db.query(DBEvaluationResult).filter(
            DBEvaluationResult.submission_id == uuid.UUID(submission_id)
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Update with faculty review
        evaluation.faculty_reviewed = True
        evaluation.faculty_feedback = request.faculty_feedback
        evaluation.faculty_reason = request.reason_for_adjustment
        
        # Handle score and feedback adjustments
        if 'overall_score' in request.adjusted_scores:
            original_score = evaluation.overall_score
            new_score = request.adjusted_scores['overall_score']
            evaluation.faculty_score_adjustment = new_score - original_score
            evaluation.overall_score = new_score
        
        if 'overall_feedback' in request.adjusted_scores:
            evaluation.ai_feedback = request.adjusted_scores['overall_feedback']
        
        # Log the adjustment reason
        logger.info(f"Faculty adjusted evaluation for submission {submission_id}: {request.reason_for_adjustment}")
        
        db.commit()
        
        return {
            "submission_id": submission_id,
            "review_status": "completed",
            "faculty_reviewed": True,
            "message": "Faculty review completed successfully"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid submission ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error in faculty review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save faculty review: {str(e)}")

# Step 7: Report Generation API
@router.get("/assignments/{assignment_id}/report")
async def generate_evaluation_report(assignment_id: str, db: Session = Depends(get_db)):
    """Generate downloadable evaluation report for all submissions of an assignment"""
    try:
        # Import report generator
        from services.report_generator import EvaluationReportGenerator
        
        # Get assignment details
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Get course details
        course = db.query(DBCourse).filter(DBCourse.id == assignment.course_id).first()
        
        # Get all evaluation results for this assignment
        evaluation_results_db = db.query(DBEvaluationResult).filter(
            DBEvaluationResult.assignment_id == uuid.UUID(assignment_id)
        ).all()
        
        if not evaluation_results_db:
            raise HTTPException(status_code=404, detail="No evaluation results found for this assignment")
        
        # Get rubric details
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.assignment_ids.contains([uuid.UUID(assignment_id)])
        ).first()
        
        if not rubric:
            raise HTTPException(status_code=404, detail="No rubric found for this assignment")
        
        # Prepare assignment data
        assignment_data = {
            'assignment_name': assignment.assignment_name,
            'title': assignment.title,
            'description': assignment.description,
            'course_title': course.title if course else 'Unknown Course',
            'academic_year': course.academic_year if course else 'N/A',
            'semester': course.semester if course else 'N/A'
        }
        
        # Prepare evaluation results data
        evaluation_results = []
        for eval_result in evaluation_results_db:
            # Get submission details
            submission = db.query(DBStudentSubmission).filter(
                DBStudentSubmission.id == eval_result.submission_id
            ).first()
            
            result_data = {
                'submission_id': str(eval_result.submission_id),
                'file_name': submission.original_file_name if submission else 'Unknown',
                'overall_score': eval_result.overall_score,
                'overall_feedback': eval_result.ai_feedback,
                'faculty_reviewed': eval_result.faculty_reviewed,
                'faculty_feedback': eval_result.faculty_feedback,
                'faculty_adjustments': {
                    'score_adjustment': eval_result.faculty_score_adjustment,
                    'reason': eval_result.faculty_reason
                } if eval_result.faculty_score_adjustment or eval_result.faculty_reason else None,
                'criterion_results': []
            }
            
            # Process criterion results
            if eval_result.criterion_scores:
                for category, details in eval_result.criterion_scores.items():
                    criterion_data = {
                        'category': category,
                        'score': details.get('score', 0),
                        'max_score': details.get('max_score', 0),
                        'percentage': details.get('percentage', 0),
                        'feedback': details.get('feedback', '')
                    }
                    result_data['criterion_results'].append(criterion_data)
            
            evaluation_results.append(result_data)
        
        # Prepare rubric data
        rubric_data = {
            'rubric_name': rubric.rubric_name,
            'doc_type': rubric.doc_type,
            'rubrics': rubric.criteria.get('rubrics', []) if isinstance(rubric.criteria, dict) else []
        }
        
        # Generate PDF report
        report_generator = EvaluationReportGenerator()
        pdf_content = report_generator.generate_evaluation_report(
            assignment_data, evaluation_results, rubric_data
        )
        
        # Return PDF as response
        from fastapi.responses import Response
        
        filename = f"evaluation_report_{assignment.assignment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

# Generate Rubric for Assignment (Step 3 - when no rubric exists)
"""
Rubric generation in evaluation flow is disabled; the system uses a hardcoded rubric
from MySQL. The previous endpoint has been intentionally removed.
"""

# Edit Rubric in Evaluation Flow (Step 3)
class RubricEditRequestEval(BaseModel):
    criteria: Dict[str, Any]
    reason_for_edit: str
    name_only_change: bool = False

@router.put("/rubric/{rubric_id}/edit")
async def edit_rubric_in_evaluation(
    rubric_id: str,
    request: RubricEditRequestEval,
    db: Session = Depends(get_db)
):
    """Edit a rubric in the evaluation flow (reuses generation page logic)"""
    try:
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.id == uuid.UUID(rubric_id)
        ).first()
        
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        # Update rubric
        rubric.rubric_name = request.criteria.get('rubric_name', rubric.rubric_name)
        rubric.doc_type = request.criteria.get('doc_type', rubric.doc_type)
        rubric.criteria = request.criteria
        
        # Only mark as edited if it's not just a name/type change
        if not request.name_only_change:
            rubric.is_edited = True
        rubric.reason_for_edit = request.reason_for_edit
        
        db.commit()
        
        return {
            "message": "Rubric updated successfully",
            "rubric_id": rubric_id,
            "is_edited": rubric.is_edited
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rubric ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error editing rubric {rubric_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to edit rubric: {str(e)}")

@router.post("/faculty/reject/{submission_id}")
async def reject_submission(
    submission_id: str,
    rejection: RejectionRequest,
    db: Session = Depends(get_db)
):
    """
    Faculty rejection of a student submission with feedback
    """
    try:
        # Get submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Update submission status and add rejection details
        submission.evaluation_status = "rejected"
        submission.rejection_reason = rejection.rejection_reason
        submission.rejection_date = datetime.utcnow()
        
        # Save to database
        db.commit()
        
        return {"message": "Submission rejected successfully"}
        
    except Exception as e:
        logger.error(f"Error rejecting submission: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error rejecting submission")

@router.post("/faculty/evaluate/{submission_id}/finalize")
async def finalize_evaluation(
    submission_id: str,
    db: Session = Depends(get_db)
):
    """
    Finalize an evaluation after score adjustments
    """
    try:
        # Get submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Update submission status
        submission.evaluation_status = "evaluated"
        
        # Get final evaluation
        eval_result = db.query(DBFacultyEvaluation).filter(
            DBFacultyEvaluation.submission_id == submission_id
        ).first()
        
        if not eval_result:
            raise HTTPException(status_code=404, detail="Evaluation not found")
            
        # Update evaluation
        eval_result.is_finalized = True
        eval_result.finalized_at = datetime.utcnow()
        
        # Save changes
        db.commit()
        
        return {"message": "Evaluation finalized successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error finalizing evaluation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to finalize evaluation: {str(e)}")

# Service Health and Status Endpoints
@router.get("/status")
async def get_service_status():
    """Get status of all evaluation services (OCR, text extraction, LLM evaluation)"""
    try:
        status = submission_processor.get_service_status()
        return status
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        return {
            "overall_status": "error",
            "error": str(e)
    }
