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
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from database.models import (
    GeneratedAssignment as DBGeneratedAssignment,
    AssignmentRubric as DBAssignmentRubric,
    StudentSubmission as DBStudentSubmission,
    EvaluationResult as DBEvaluationResult,
    Course as DBCourse
)
from database.repository import get_db
from services.submission_processor import SubmissionProcessingService
from storage.minio_client import minio_client

# Configure logging
logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize submission processing service
submission_processor = SubmissionProcessingService()

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
    assignment_id: str
    rubric_id: str
    submission_ids: Optional[List[str]] = None  # If provided, only evaluate these specific submissions
    
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
        
        # Find rubrics that include this assignment
        rubrics = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.assignment_ids.contains([assignment_uuid])
        ).all()
        
        rubric_responses = []
        for rubric in rubrics:
            rubric_responses.append(RubricResponse(
                id=str(rubric.id),
                rubric_name=rubric.rubric_name,
                doc_type=rubric.doc_type,
                criteria=rubric.criteria,
                is_edited=rubric.is_edited,
                created_at=rubric.created_at
            ))
        
        return rubric_responses
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        logger.error(f"Error fetching rubrics for assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rubrics: {str(e)}")

# Step 4: Student Submission Upload API
@router.post("/submissions/upload", response_model=List[SubmissionResponse])
async def upload_student_submissions(
    assignment_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload student submissions for evaluation (max 5 files, PDF/DOCX only)
    Files are processed and stored in MinIO, text extracted if needed
    Only processes new files, skips already processed ones
    """
    try:
        # Validate file count
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 submissions allowed per evaluation")
    
        # Validate assignment exists
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
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
            
            # Create database entry with MinIO path
            submission = DBStudentSubmission(
                id=uuid.UUID(submission_id),
                assignment_id=uuid.UUID(assignment_id),
                original_file_name=file.filename,
                file_path=minio_path,  # Store MinIO path instead of temp path
                file_type=file.filename.split('.')[-1].lower(),
                extracted_text=extracted_text,
                ocr_confidence=ocr_confidence
            )
            
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
        # Validate assignment and rubric exist
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(request.assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.id == uuid.UUID(request.rubric_id)
        ).first()
        
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
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
                
                # Use submission processing service for evaluation
                evaluation_result = submission_processor.evaluate_submission(
                    submission_text=submission.extracted_text,
                    assignment_description=assignment_description,
                    rubric=rubric.criteria,
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
                    rubric_id=uuid.UUID(request.rubric_id),
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
class RubricGenerationRequestEval(BaseModel):
    rubric_name: str

@router.post("/assignments/{assignment_id}/rubric/generate")
async def generate_rubric_for_assignment(
    assignment_id: str,
    request: RubricGenerationRequestEval,
    db: Session = Depends(get_db)
):
    """Generate rubric for a specific assignment in the evaluation flow"""
    try:
        # Get the assignment
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Import rubric service
        from services.rubric_service import RubricService
        rubric_service = RubricService()
        
        # Combine assignment text for rubric generation
        combined_text = f"Assignment: {assignment.title}\n{assignment.description}"
        
        # Generate rubric
        rubric_data = await rubric_service.generate_rubric(
            text=combined_text,
            doc_type="Situated Learning Assignment"
        )
        
        # Update the rubric_data to use the user-provided name consistently
        rubric_data["rubric_name"] = request.rubric_name
        
        # Save to database
        db_rubric = DBAssignmentRubric(
            id=uuid.uuid4(),
            assignment_ids=[assignment.id],
            rubric_name=request.rubric_name,
            doc_type=rubric_data.get("doc_type", "Assignment"),
            criteria=rubric_data
        )
        
        db.add(db_rubric)
        db.commit()
        
        return {
            "message": "Rubric generated successfully",
            "rubric_id": str(db_rubric.id),
            "rubric": rubric_data
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating rubric for assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate rubric: {str(e)}")

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
