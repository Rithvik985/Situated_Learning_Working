"""
Faculty workflow router: manage student assignments, approvals, and evaluations
"""
import os
import sys
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import json
import time
import logging
logger = logging.getLogger(__name__)

from database.repository import get_db
from database.models import (
    StudentQuestionSet as DBStudentQuestionSet, 
    EvaluationResult as DBEvaluationResult,
    Course as DBCourse,
    StudentSubmission as DBStudentSubmission,
    GeneratedAssignment as DBGeneratedAssignment,
    FacultyEvaluationResult as DBFacultyEvaluation
)
from services.evaluation_service import EvaluationService, SITUATED_LEARNING_RUBRIC
from schemas.schemas import AutoEvaluateResponse, AutoEvaluateRequest
from services.radar_service import RadarService
from typing import Dict, Any

router = APIRouter()
radar_service = RadarService()


@router.get("/pending-submissions")
async def get_pending_submissions(db: Session = Depends(get_db)):
    """Get all submissions pending faculty evaluation"""
    try:
        submissions = (
            db.query(DBStudentSubmission)
            .filter(DBStudentSubmission.evaluation_status == "pending_faculty")
            .order_by(DBStudentSubmission.created_at.desc())
            .all()
        )

        result = [
            {
                "id": str(sub.id),
                "student_id": sub.student_id,
                "assignment_id": str(sub.assignment_id),
                "submission_date": sub.created_at.isoformat() if sub.created_at else None,
                "evaluation_status": sub.evaluation_status,
            }
            for sub in submissions
        ]

        logger.info(f"Found {len(result)} pending submissions")
        return result

    except Exception as e:
        logger.error(f"Error fetching pending submissions: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch pending submissions"
        )


class ApprovalRequest(BaseModel):
    approve: bool
    remarks: Optional[str] = None
    faculty_id: Optional[str] = None
    rejection_reason: Optional[str] = None

class CriterionScoreUpdate(BaseModel):
    criterion_id: str
    new_score: float
    faculty_id: str

class StudentAssignment(BaseModel):
    approve: bool
    remarks: Optional[str] = None
    faculty_id: Optional[str] = None
    rejection_reason: Optional[str] = None

class StudentAssignment(BaseModel):
    id: str
    student_id: str

class SubmissionDetail(BaseModel):
    id: str
    student_id: str
    content: str
    submission_date: str
    evaluation_status: str
    assignment_details: Dict[str, Any]
    current_evaluation: Optional[Dict[str, Any]] = None

class EvaluationRequest(BaseModel):
    submission_id: str
    criteria_scores: Dict[str, float]
    feedback: str
    faculty_id: Optional[str]='f20220162'

class RubricDimension(BaseModel):
    name: str
    criteria: Dict[str, str]
    score_description: Dict[str, Dict[str, str]]
    max_score: float = 4.0

@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission_details(
    submission_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed view of a student submission including current evaluation if it exists
    """
    try:
        # Get submission with related assignment
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Get current evaluation if it exists
        current_eval = db.query(DBFacultyEvaluation).filter(
            DBFacultyEvaluation.submission_id == submission_id
        ).first()

        # Get assignment details
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == submission.assignment_id
        ).first()

        return SubmissionDetail(
            id=str(submission.id),
            student_id=submission.student_id,
            content=submission.content,
            submission_date=submission.created_at.isoformat(),
            evaluation_status=submission.evaluation_status,
            assignment_details={
                "title": assignment.title if assignment else None,
                "description": assignment.description if assignment else None,
                "course_name": assignment.course_name if assignment else None
            },
            current_evaluation={
                "criteria_scores": current_eval.rubric_scores if current_eval else None,
                "feedback": current_eval.comments if current_eval else None,
                "evaluation_date": current_eval.evaluation_date.isoformat() if current_eval else None
            } if current_eval else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rubric", response_model=Dict[str, Any])
async def get_evaluation_rubric():
    """
    Get the evaluation rubric structure
    """
    try:
        return SITUATED_LEARNING_RUBRIC
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/submissions/{submission_id}/evaluate")
async def evaluate_submission(
    submission_id: str,
    evaluation: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Create or update faculty evaluation for a submission
    Accepts flattened criteria_scores with keys like "Dimension > Criterion" => score
    """
    try:
        logger.info(f"=== evaluate_submission called ===")
        logger.info(f"submission_id (from URL): {submission_id}")
        logger.info(f"evaluation.submission_id (from body): {evaluation.submission_id}")
        logger.info(f"criteria_scores: {evaluation.criteria_scores}")
        logger.info(f"feedback: {evaluation.feedback}")
        logger.info(f"faculty_id: {evaluation.faculty_id}")  # Log faculty_id
        
        # Convert submission_id to UUID if needed
        try:
            submission_uuid = uuid.UUID(submission_id)
        except ValueError:
            logger.error(f"Invalid UUID format for submission_id: {submission_id}")
            raise HTTPException(status_code=400, detail=f"Invalid submission ID format: {submission_id}")
        
        # Verify submission exists
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_uuid
        ).first()
        
        logger.info(f"Submission query result: {submission}")
        if not submission:
            logger.error(f"Submission not found: {submission_uuid}")
            raise HTTPException(status_code=404, detail=f"Submission not found: {submission_uuid}")

        # Check if evaluation already exists
        existing_eval = db.query(DBFacultyEvaluation).filter(
            DBFacultyEvaluation.submission_id == submission_id
        ).first()

        # If criteria_scores are flat keys like "Dimension > Criterion", transform into nested structure
        criteria = evaluation.criteria_scores or {}
        nested = {}
        for k, v in criteria.items():
            if isinstance(k, str) and '>' in k:
                dim, crit = [part.strip() for part in k.split('>', 1)]
                nested.setdefault(dim, []).append({"question": crit, "score": v})
            else:
                # Legacy: treat top-level keys as dimension categories with a numeric value
                nested.setdefault(k, []).append({"question": None, "score": v})

        # Build rubric_scores list with per-question entries and compute totals
        rubric_scores_list = []
        total_score = 0
        for dim_name, qlist in nested.items():
            q_results = []
            dim_total = 0
            for q in qlist:
                score_val = float(q.get('score') or 0)
                dim_total += score_val
                q_results.append({
                    "question": q.get('question'),
                    "score": score_val,
                    "feedback": None
                })
            rubric_scores_list.append({
                "category": dim_name,
                "score": dim_total,
                "max_score": len(qlist) * 4,
                "percentage": (dim_total / (len(qlist) * 4) * 100) if len(qlist) > 0 else 0,
                "question_results": q_results
            })
            total_score += dim_total

        # 🔥 CRITICAL FIX: Ensure faculty_id is properly set
        faculty_id = evaluation.faculty_id
        if not faculty_id:
            # Provide a default faculty ID if none provided
            faculty_id = "f20220162"  # TODO: Replace with actual faculty ID from auth
            logger.warning(f"No faculty_id provided, using default: {faculty_id}")

        if existing_eval:
            # Update existing evaluation
            existing_eval.rubric_scores = rubric_scores_list
            existing_eval.comments = evaluation.feedback
            existing_eval.faculty_id = faculty_id  # Make sure this is set
            existing_eval.evaluation_date = datetime.utcnow()
            logger.info(f"Updated existing evaluation with faculty_id: {faculty_id}")
        else:
            # Create new evaluation - THIS WAS MISSING faculty_id!
            new_eval = DBFacultyEvaluation(
                id=str(uuid.uuid4()),
                submission_id=submission_id,
                faculty_id=faculty_id,  # 🔥 THIS WAS THE MISSING LINE!
                rubric_scores=rubric_scores_list,
                comments=evaluation.feedback,
                evaluation_date=datetime.utcnow()
            )
            db.add(new_eval)
            logger.info(f"Created new evaluation with faculty_id: {faculty_id}")

        # Update submission status and score
        submission.evaluation_status = "evaluated"
        submission.evaluation_score = total_score
        db.commit()

        logger.info(f"✅ Evaluation saved successfully for submission {submission_id}")
        logger.info(f"→ faculty_id: {faculty_id}")
        logger.info(f"→ total_score: {total_score}")

        return {"message": "Evaluation saved successfully", "total_score": total_score}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error in evaluate_submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class CourseInfo(BaseModel):
    id: str
    course_code: str
    title: str

class QuestionSetItem(BaseModel):
    id: str
    student_id: str
    domain: str
    service_category: Optional[str] = None
    department: Optional[str] = None
    selected_question: Optional[str] = None
    approval_status: str

class EvaluationScores(BaseModel):
    scores: Dict[str, float]


# Get available courses
@router.get("/courses", response_model=List[CourseInfo])
async def get_courses(db: Session = Depends(get_db)):
    """Get all available courses"""
    try:
        courses = db.query(DBCourse).all()
        return [
            CourseInfo(
                id=str(course.id),
                course_code=course.course_code,
                title=course.title
            )
            for course in courses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get students by course
@router.get("/students", response_model=List[StudentAssignment])
async def get_students_by_course(course_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all student assignments, optionally filtered by course"""
    try:
        query = db.query(DBStudentQuestionSet)
        if course_id:
            query = query.filter(DBStudentQuestionSet.course_id == uuid.UUID(course_id))
        
        assignments = query.all()
        
        return [
            StudentAssignment(
                id=str(assignment.id),
                student_id=assignment.student_id,
                course_id=str(assignment.course_id),
                course_name=assignment.course.title if assignment.course else "",
                domain=assignment.domain,
                assignment_text=assignment.selected_question or "",
                approval_status=assignment.approval_status,
                evaluation_status=bool(
                    db.query(DBEvaluationResult)
                    .filter(DBEvaluationResult.submission_id == assignment.id)
                    .first()
                )
            )
            for assignment in assignments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/questions", response_model=List[QuestionSetItem])
async def list_question_sets(status: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(DBStudentQuestionSet)
        if status:
            query = query.filter(DBStudentQuestionSet.approval_status == status)
        rows = query.order_by(DBStudentQuestionSet.created_at.desc()).limit(100).all()
        return [
            QuestionSetItem(
                id=str(r.id),
                student_id=r.student_id,
                domain=r.domain,
                service_category=r.service_category,
                department=r.department,
                selected_question=r.selected_question,
                approval_status=r.approval_status,
            ) for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/questions/{question_set_id}/approve")
async def approve_question(question_set_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    try:
        row = db.query(DBStudentQuestionSet).filter(DBStudentQuestionSet.id == uuid.UUID(question_set_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Question set not found")
        if not row.selected_question:
            raise HTTPException(status_code=400, detail="No selected question to approve")

        row.approval_status = 'approved' if req.approve else 'rejected'
        row.faculty_remarks = req.remarks
        row.approved_by = req.faculty_id
        db.commit()
        return {
            "id": str(row.id),
            "approval_status": row.approval_status,
            "remarks": row.faculty_remarks
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class FinalizeMarksRequest(BaseModel):
    submission_id: str
    final_marks: float
    final_feedback: Optional[str] = None

class EvaluationData(BaseModel):
    criteria: List[Dict[str, Any]]
    overall_score: float

@router.get("/evaluation/{assignment_id}")
async def get_evaluation_data(assignment_id: str, db: Session = Depends(get_db)):
    """Get evaluation data for an assignment"""
    try:
        evaluation = db.query(DBEvaluationResult).filter(
            DBEvaluationResult.submission_id == uuid.UUID(assignment_id)
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return {
            "criteria": [
                {
                    "id": criterion["id"],
                    "name": criterion["name"],
                    "description": criterion["description"],
                    "max_score": criterion["max_score"],
                    "score": criterion["score"]
                }
                for criterion in evaluation.criteria_scores
            ] if evaluation.criteria_scores else [],
            "overall_score": evaluation.overall_score
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/evaluation/update/{assignment_id}")
async def update_evaluation(assignment_id: str, scores: EvaluationScores, db: Session = Depends(get_db)):
    """Update evaluation scores for an assignment"""
    try:
        evaluation = db.query(DBEvaluationResult).filter(
            DBEvaluationResult.submission_id == uuid.UUID(assignment_id)
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Update individual criterion scores
        if evaluation.criteria_scores:
            updated_scores = evaluation.criteria_scores.copy()
            for criterion in updated_scores:
                if criterion["id"] in scores.scores:
                    criterion["score"] = scores.scores[criterion["id"]]
            evaluation.criteria_scores = updated_scores
        
        # Recalculate overall score
        evaluation.overall_score = sum(
            criterion["score"] for criterion in evaluation.criteria_scores
        ) if evaluation.criteria_scores else 0
        
        db.commit()
        return {"status": "success", "message": "Evaluation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/finalize")
async def finalize_marks(req: FinalizeMarksRequest, db: Session = Depends(get_db)):
    """
    Finalize the faculty evaluation of a submission.
    This marks the evaluation as complete and stores the final score.
    """
    try:
        logger.info(f"=== Finalize evaluation ===")
        logger.info(f"submission_id: {req.submission_id}")
        logger.info(f"final_marks: {req.final_marks}")
        
        submission_uuid = uuid.UUID(req.submission_id)
        
        # Get the submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == submission_uuid
        ).first()
        
        if not submission:
            logger.error(f"Submission not found: {submission_uuid}")
            raise HTTPException(status_code=404, detail=f"Submission not found: {submission_uuid}")
        
        # Get the faculty evaluation (most recent one)
        faculty_eval = db.query(DBFacultyEvaluation).filter(
            DBFacultyEvaluation.submission_id == submission_uuid
        ).order_by(DBFacultyEvaluation.evaluation_date.desc()).first()
        
        if not faculty_eval:
            logger.error(f"Faculty evaluation not found for submission: {submission_uuid}")
            raise HTTPException(status_code=404, detail=f"Faculty evaluation not found for submission: {submission_uuid}")
        
        # Update faculty evaluation to mark as finalized
        logger.info(f"Marking faculty evaluation {faculty_eval.id} as finalized")
        
        # Update submission with final score and status
        submission.evaluation_score = req.final_marks
        submission.evaluation_status = "finalized"
        
        # Store finalization metadata on faculty evaluation
        faculty_eval.comments = req.final_feedback or faculty_eval.comments
        
        db.commit()
        
        logger.info(f"✅ Evaluation finalized successfully")
        logger.info(f"→ submission_id: {submission_uuid}")
        logger.info(f"→ final_marks: {req.final_marks}")
        logger.info(f"→ evaluation_status: {submission.evaluation_status}")
        
        return {
            "submission_id": str(submission_uuid),
            "final_marks": req.final_marks,
            "status": "finalized",
            "message": "Evaluation finalized successfully"
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid submission ID format: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error finalizing evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/student/{student_id}", response_model=List[QuestionSetItem])
async def get_questions_by_student(student_id: str, db: Session = Depends(get_db)):
    """Get all question sets submitted by a specific student"""
    try:
        rows = db.query(DBStudentQuestionSet).filter(
            DBStudentQuestionSet.student_id == student_id
        ).order_by(DBStudentQuestionSet.created_at.desc()).all()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No question sets found for this student")
        
        return [
            QuestionSetItem(
                id=str(r.id),
                student_id=r.student_id,
                domain=r.domain,
                service_category=r.service_category,
                department=r.department,
                selected_question=r.selected_question,
                approval_status=r.approval_status
            )
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import JSONResponse

@router.put("/evaluate/{submission_id}/criterion/{criterion_id}")
async def update_criterion_score(
    submission_id: str,
    criterion_id: str,
    update: CriterionScoreUpdate,
    db: Session = Depends(get_db)
):
    """
    Update individual criterion score for a submission (faculty manual adjustment)
    """
    try:
        eval_result = db.query(DBFacultyEvaluation).filter(
            DBFacultyEvaluation.submission_id == submission_id
        ).first()

        if not eval_result:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # Round score
        new_score = round(update.new_score * 4) / 4
        new_score = max(1.0, min(4.0, new_score))

        rubric_scores = eval_result.rubric_scores

        # ✅ Case 1: Rubric is list of categories (correct structure)
        if isinstance(rubric_scores, list):
            for item in rubric_scores:
                if str(item.get("category")) == str(criterion_id):
                    item["score"] = new_score
                    break
            else:
                # if not found, append it (failsafe)
                rubric_scores.append({"category": criterion_id, "score": new_score})

            # ✅ Recalculate total
            total_score = sum(i.get("score", 0) for i in rubric_scores)
            eval_result.rubric_scores = rubric_scores

        # ✅ Case 2: Rubric is dict (legacy)
        elif isinstance(rubric_scores, dict):
            rubric_scores[criterion_id] = new_score
            total_score = sum(rubric_scores.values())
            eval_result.rubric_scores = rubric_scores

        else:
            raise HTTPException(status_code=400, detail="Invalid rubric_scores format")

        # ✅ Update DB record correctly
        eval_result.evaluation_score = total_score
        eval_result.last_updated = datetime.utcnow()
        db.commit()

        return {
            "criterion_id": criterion_id,
            "new_score": new_score,
            "total_score": total_score
        }

    except Exception as e:
        logger.exception("Error updating criterion score")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating score: {str(e)}")



@router.post("/submissions/{submission_id}/detect-ai", response_model=Dict[str, Any])
async def detect_ai_content(submission_id: str, db: Session = Depends(get_db)):
    """
    Analyze a submission for potential AI-generated content using RADAR
    """
    try:
        submission = db.query(DBStudentSubmission).filter(DBStudentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Get AI detection analysis
        analysis_results = await radar_service.analyze_submission(submission.content)
        
        # Update the submission with AI detection results
        submission.ai_detection_results = analysis_results
        db.commit()
        
        return analysis_results
    except Exception as e:
        logger.error(f"Error during AI detection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze submission for AI content")

@router.post("/pending-submissions/{submission_id}/evaluate")
async def auto_evaluate_submission(submission_id: str, request: AutoEvaluateRequest, db: Session = Depends(get_db)):
    """
    Automatically evaluate a student's submission using LLM-based rubric analysis.
    Triggered when a faculty member clicks 'Evaluate'.
    """
    try:
        # Log incoming request
        logger.info(f"📥 auto_evaluate_submission() called with submission_id: {submission_id}")
        logger.info(f"📤 Response model: AutoEvaluateResponse")
        
        # Step 1: Fetch submission
        submission = db.query(DBStudentSubmission).filter(DBStudentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Step 2: Ensure status is correct
        if submission.evaluation_status != "pending_faculty":
            raise HTTPException(
                status_code=400,
                detail=str(f"Submission not ready for evaluation (current status: {submission.evaluation_status})")
            )

        # Step 3: Fetch the linked assignment context
        assignment = db.query(DBGeneratedAssignment).filter(DBGeneratedAssignment.id == submission.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Linked assignment not found")

        assignment_description = (
            f"Title: {assignment.title}\n"
            f"Description: {assignment.description}\n"
            f"Requirements: {', '.join(assignment.requirements or [])}\n"
            f"Context: {assignment.industry_context or 'No industry context provided.'}"
        )

        # Step 4: Use student's submission content
        submission_text = submission.content or "No content submitted."

        # Step 5: Prepare rubric
        rubric = {"rubrics": [
            {"category": dim["name"], "questions": list(dim["criteria_output"].keys())}
            for dim in SITUATED_LEARNING_RUBRIC["dimensions"]
        ]}

        # Step 6: Run EvaluationService
        evaluator = EvaluationService()
        start = time.time()
        evaluation_result = evaluator.evaluate_submission(
            assignment_description=assignment_description,
            submission_text=submission_text,
            rubric=rubric,
            submission_id=submission_id
        )
        duration = round(time.time() - start, 2)

        # Log evaluation results
        logger.info("=== Evaluation Results Processing ===")
        logger.info(f"Raw evaluation result - overall score: {evaluation_result.overall_score}/72")
        logger.info("Criterion evaluations:")
        for ce in evaluation_result.criterion_evaluations:
            logger.info(f"- {ce.category}:")
            logger.info(f"  Score: {ce.score}/{ce.max_score}")
            logger.info(f"  Percentage: {ce.percentage:.1f}%")
            for qr in ce.question_results:
                logger.info(f"  - Question: {qr.question}, Score: {qr.score}")

        # Step 7: Store faculty evaluation (include question-level results so frontend can edit them)
        rubric_scores = []
        for ce in evaluation_result.criterion_evaluations:
            question_results = [
                {"question": qr.question, "score": qr.score, "feedback": qr.reasoning}
                for qr in ce.question_results
            ]
            rubric_scores.append({
                "category": ce.category,
                "score": ce.score,
                "max_score": ce.max_score,
                "percentage": ce.percentage,
                "feedback": ce.feedback,
                "question_results": question_results,
            })

        # 🔥 FIX: Use faculty_id from request or provide default
        faculty_id = getattr(request, 'faculty_id', "f20220162")
        
        faculty_eval = DBFacultyEvaluation(
            submission_id=submission_id,
            faculty_id=faculty_id,  # Make sure this is set
            rubric_scores=rubric_scores,
            comments=evaluation_result.overall_feedback,
            evaluation_date=datetime.utcnow()
        )
        db.add(faculty_eval)

        # Step 8: Update submission status + score
        submission.evaluation_status = "evaluated"
        submission.evaluation_score = evaluation_result.overall_score
        db.commit()

        logger.info(f"✅ Auto evaluation done for submission {submission_id} | Score: {evaluation_result.overall_score}/72")

        # Step 9: Build rich response with structured dimensions and criteria
        dimensions = []
        for ce in evaluation_result.criterion_evaluations:
            criteria_list = []
            # Build individual criteria with scores and feedback
            for qr in ce.question_results:
                criteria_list.append({
                    "name": qr.question,
                    "score": qr.score,
                    "feedback": qr.reasoning or "No specific feedback provided."
                })
            
            dimensions.append({
                "name": ce.category,
                "dimension_score": float(ce.score),
                "dimension_max_score": float(ce.max_score),
                "dimension_percentage": round(ce.percentage, 2),
                "dimension_feedback": ce.feedback,
                "criteria": criteria_list
            })

        # Build the final response payload
        response_payload = {
            "submission_id": submission_id,
            "status": "evaluated",
            "overall_score": evaluation_result.overall_score,
            "total_criteria": evaluation_result.total_criteria,
            "overall_feedback": evaluation_result.overall_feedback,
            "processing_time": evaluation_result.processing_time,
            "llm_model": evaluation_result.evaluation_metadata.get("model_used"),
            "duration": duration,
            "dimensions": dimensions,
            "evaluation_metadata": evaluation_result.evaluation_metadata
        }

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Auto evaluation failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
    

class FacultyDashboardItem(BaseModel):
    id: str
    student_id: str
    student_email: Optional[str] = None
    course_name: Optional[str] = None
    domain: str
    service_category: Optional[str] = None
    department: Optional[str] = None
    selected_question: Optional[str] = None
    approval_status: str
    evaluation_status: Optional[str] = None
    evaluation_score: Optional[float] = None
    submission_id: Optional[str] = None
    submission_date: Optional[str] = None

@router.get("/dashboard", response_model=List[FacultyDashboardItem])
async def get_faculty_dashboard(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard data with all student submissions and evaluations
    """
    try:
        # Get all student question sets
        question_sets = db.query(DBStudentQuestionSet).order_by(
            DBStudentQuestionSet.created_at.desc()
        ).all()
        
        result = []
        for qs in question_sets:
            # Get the most recent submission for this student
            submission = db.query(DBStudentSubmission).filter(
                DBStudentSubmission.student_id == qs.student_id
            ).order_by(DBStudentSubmission.created_at.desc()).first()
            
            # Get course info if available
            course_name = None
            if qs.course_id:
                course = db.query(DBCourse).filter(DBCourse.id == qs.course_id).first()
                course_name = course.title if course else None
            
            # Get evaluation status and score from submission
            evaluation_status = None
            evaluation_score = None
            submission_id = None
            submission_date = None
            
            if submission:
                evaluation_status = submission.evaluation_status
                evaluation_score = submission.evaluation_score
                submission_id = str(submission.id)
                submission_date = submission.created_at.isoformat() if submission.created_at else None
            
            result.append(FacultyDashboardItem(
                id=str(qs.id),
                student_id=qs.student_id,
                student_email=qs.student_id,  # Using student_id as email if separate email not available
                course_name=course_name,
                domain=qs.domain,
                service_category=qs.service_category,
                department=qs.department,
                selected_question=qs.selected_question,
                approval_status=qs.approval_status,
                evaluation_status=evaluation_status,
                evaluation_score=evaluation_score,
                submission_id=submission_id,
                submission_date=submission_date
            ))
        
        logger.info(f"✅ Faculty dashboard data fetched: {len(result)} items")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching faculty dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")