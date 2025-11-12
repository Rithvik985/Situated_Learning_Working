"""
Student workflow router: context selection, question generation, selection, AI check loop
"""
import os
import sys
from uuid import UUID, uuid4
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
import json

logger = logging.getLogger(__name__)

from database.repository import get_db
from database.models import (
    StudentQuestionSet as DBStudentQuestionSet, 
    Course as DBCourse,
    StudentSubmission as DBStudentSubmission,
    GeneratedAssignment as DBGeneratedAssignment,
    StudentSWOTResult as DBStudentSWOT,
    FacultyEvaluationResult as DBFacultyEvaluation
)
from schemas.student import SaveAssignmentRequest
from utils.llm_config import llm_config
from openai import OpenAI

class SavedAssignment(BaseModel):
    """Response model for saved assignments"""
    id: str
    title: str
    description: str
    assignment_name: str
    created_at: datetime
    domain: Optional[str]
    course_name: Optional[str]

class SWOTAnalysis(BaseModel):
    """SWOT analysis model"""
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    suggestions: List[str]
    submission_id: Optional[str] = None

class SWOTRequest(BaseModel):
    """Request model for SWOT analysis"""
    student_id: str
    assignment_id: str
    content: str

class SubmitToFacultyRequest(BaseModel):
    """Request model for submitting to faculty"""
    student_id: str
    submission_id: str
from services.llm_service import LLMService
from services.evaluation_service import EvaluationService, SITUATED_LEARNING_RUBRIC
# from services.student_service import save_student_assignment
from services.swot_service import LLMAnalysisService

from pydantic import BaseModel
from typing import List, Optional

class SWOTRequest(BaseModel):
    student_id: str
    assignment_id: str
    content: str

class SWOTAnalysis(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    suggestions: List[str]
    submission_id: Optional[str] = None  # Added to track submission

class QuestionSelectionRequest(BaseModel):
    selected_question: str

router = APIRouter()

logger = logging.getLogger(__name__)

# Initialize the LLM service
llm_service = LLMAnalysisService()

@router.post("/analyze", response_model=SWOTAnalysis)
async def analyze_submission(request: SWOTRequest, db: Session = Depends(get_db)):
    """
    Perform SWOT analysis on a student's submission using LLM.
    Creates a submission first, then runs SWOT and links it.
    """
    try:
        # Step 1: Create submission FIRST
        new_submission = DBStudentSubmission(
            student_id=request.student_id,
            assignment_id=request.assignment_id,
            course_id=db.query(DBGeneratedAssignment.course_id)
                        .filter(DBGeneratedAssignment.id == request.assignment_id)
                        .scalar(),
            content=request.content,
            evaluation_status="draft",
            processing_status="processing"
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        # Step 2: Run LLM SWOT with submission_id
        swot_data = await llm_service.analyze_submission(
            request=request,
            db=db,
            submission_id=str(new_submission.id)  # ✅ pass ID explicitly
        )
        swot_data["submission_id"] = str(swot_data["submission_id"])  # ✅ convert UUID to string

        # Step 3: Save SWOT data inside submission
        new_submission.swot_analysis = swot_data
        new_submission.processing_status = "completed"
        db.commit()
        db.refresh(new_submission)
        logger.info(f"Final SWOT data before returning: {json.dumps(swot_data, indent=2)}")

        # Step 4: Return SWOT + submission_id
        return SWOTAnalysis(
            strengths=swot_data.get("strengths", []),
            weaknesses=swot_data.get("weaknesses", []),
            opportunities=swot_data.get("opportunities", []),
            threats=swot_data.get("threats", []),
            suggestions=swot_data.get("suggestions", []),
            submission_id=str(new_submission.id)
        )

    except Exception as e:
        logger.error(f"Error analyzing submission: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to analyze submission: {str(e)}")


@router.post("/submit-to-faculty")
async def submit_to_faculty(request: SubmitToFacultyRequest, db: Session = Depends(get_db)):
    """
    Submit final version for faculty evaluation
    """
    try:
        # Get the submission
        submission = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.id == request.submission_id,
            DBStudentSubmission.student_id == request.student_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
            
        # Update submission status
        submission.evaluation_status = "pending_faculty"
        db.commit()
        
        return {"message": "Submission sent for faculty evaluation"}
        
    except Exception as e:
        logger.error(f"Error submitting to faculty: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-submissions/{student_id}")
async def get_my_submissions(student_id: str, db: Session = Depends(get_db)):
    """
    Get all submissions for a student with their evaluation status and history
    """
    try:
        submissions = db.query(DBStudentSubmission).filter(
            DBStudentSubmission.student_id == student_id
        ).all()
        
        results = []
        for sub in submissions:
            # Get all SWOT analyses for this submission
            swot_analyses = db.query(DBStudentSWOT).filter(
                DBStudentSWOT.submission_id == sub.id
            ).order_by(DBStudentSWOT.analysis_date.desc()).all()
            
            # Get faculty evaluation if exists
            faculty_eval = db.query(DBFacultyEvaluation).filter(
                DBFacultyEvaluation.submission_id == sub.id
            ).first()
            
            # Convert SWOT analyses to dictionaries
            swot_data = []
            for swot in swot_analyses:
                swot_data.append({
                    "id": str(swot.id),
                    "submission_id": str(swot.submission_id),
                    "strengths": swot.strengths,
                    "weaknesses": swot.weaknesses,
                    "opportunities": swot.opportunities,
                    "threats": swot.threats,
                    "suggestions": swot.suggestions,
                    "analysis_date": swot.analysis_date.isoformat() if swot.analysis_date else None
                })
            
            # Convert faculty evaluation to dictionary
            faculty_eval_data = None
            if faculty_eval:
                faculty_eval_data = {
                    "id": str(faculty_eval.id),
                    "submission_id": str(faculty_eval.submission_id),
                    "faculty_id": faculty_eval.faculty_id,
                    "rubric_scores": faculty_eval.rubric_scores,
                    "comments": faculty_eval.comments,
                    "evaluation_date": faculty_eval.evaluation_date.isoformat() if faculty_eval.evaluation_date else None
                }
            
            # Get assignment details
            assignment = db.query(DBGeneratedAssignment).filter(
                DBGeneratedAssignment.id == sub.assignment_id
            ).first()
            
            # Get course details
            course = None
            if assignment and assignment.course_id:
                course = db.query(DBCourse).filter(DBCourse.id == assignment.course_id).first()
            
            results.append({
                "id": str(sub.id),
                "assignment_id": str(sub.assignment_id),
                "assignment_title": assignment.title if assignment else "Unknown Assignment",
                "course_name": course.title if course else "Unknown Course",
                "content": sub.content,
                "status": sub.evaluation_status,
                "submission_date": sub.created_at.isoformat() if sub.created_at else None,
                "evaluation_score": sub.evaluation_score,
                "swot_analyses": swot_data,
                "faculty_evaluation": faculty_eval_data
            })
            
        return results
        
    except Exception as e:
        logger.error(f"Error fetching submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses")
async def list_student_courses(db: Session = Depends(get_db)):
    """List all available courses for students"""
    try:
        courses = db.query(DBCourse).all()
        return [
            {"id": str(c.id), "title": c.title, "course_code": c.course_code}
            for c in courses
        ]
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assignments/save")
async def save_assignment(
    request: SaveAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Save a student's selected assignment and mark their choice"""
    try:
        # Get the question set to verify it's approved
        question_set = db.query(DBStudentQuestionSet).filter(
            DBStudentQuestionSet.id == UUID(request.question_set_id)
        ).first()
        
        if not question_set:
            raise HTTPException(status_code=404, detail="Question set not found")
        
        if question_set.approval_status != 'approved':
            raise HTTPException(
                status_code=400,
                detail="Assignment must be approved before saving"
            )

        if question_set.student_id != request.student_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot save another student's assignment"
            )

        # Create a new generated assignment for the student
        new_assignment = DBGeneratedAssignment(
            id=uuid4(),
            title=f"Student Assignment - {question_set.domain}",
            description=question_set.selected_question,
            course_id=question_set.course_id if hasattr(question_set, 'course_id') else None,
            course_name=request.course_name,
            domains=[question_set.domain],
            requirements=[],
            assignment_name=request.assignment_name,
            is_selected=True,
            created_by=request.student_id
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        # Mark the question set as saved
        question_set.assignment_id = new_assignment.id
        db.commit()
        
        return {
            "message": f"Assignment '{request.assignment_name}' saved successfully",
            "assignment_id": str(new_assignment.id),
            "question_set_id": request.question_set_id
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving student assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save assignment: {str(e)}")


class ContextOptionsResponse(BaseModel):
    domains: List[str]
    service_categories: List[str]
    departments: List[str]



@router.get("/context-options", response_model=ContextOptionsResponse)
async def get_context_options():
    return ContextOptionsResponse(
        domains=[
            "Manufacturing", "IT", "Healthcare", "Finance", "Education", "Telecommunications",
            "Aerospace", "Retail", "Energy", "Government"
        ],
        service_categories=["DevOps", "ERP", "Cloud", "Data Engineering", "Cybersecurity", "QA"],
        departments=["R&D", "Operations", "Sales", "HR", "Finance", "IT"]
    )


@router.get("/assignments", response_model=List[SavedAssignment])
async def list_saved_assignments(
    student_id: str,
    db: Session = Depends(get_db)
):
    """List all assignments saved by a student"""
    try:
        # Find all assignments created by this student
        assignments = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.created_by == student_id,
            DBGeneratedAssignment.is_selected == True
        ).order_by(DBGeneratedAssignment.created_at.desc()).all()

        return [
            SavedAssignment(
                id=str(assignment.id),
                title=assignment.title,
                description=assignment.description,
                assignment_name=assignment.assignment_name,
                created_at=assignment.created_at,
                domain=assignment.domains[0] if assignment.domains else None,
                course_name=assignment.course_name
            ) for assignment in assignments
        ]

    except Exception as e:
        logger.error(f"Error listing saved assignments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list saved assignments: {str(e)}"
        )


class QuestionGenerationRequest(BaseModel):
    student_id: str
    course_id: Optional[str]
    course_name: Optional[str]
    domain: str
    service_category: Optional[str]
    department: Optional[str]
    handouts: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    custom_instructions: Optional[str] = None


class QuestionSetResponse(BaseModel):
    id: str
    student_id: str
    course_id: Optional[str]
    domain: str
    service_category: Optional[str]
    department: Optional[str]
    generated_questions: List[str]
    selected_question: Optional[str]
    approval_status: str
    faculty_remarks: Optional[str]=None
    created_at: datetime


def _find_or_create_course(db: Session, course_name: Optional[str], course_id: Optional[str]) -> Optional[DBCourse]:
    if not (course_name or course_id):
        return None
    if course_id:
        course = db.query(DBCourse).filter(DBCourse.course_code == course_id).first()
        if course:
            return course
    if course_name:
        course = db.query(DBCourse).filter(DBCourse.title == course_name).first()
        if course:
            return course
        # Minimal create with defaults
        course = DBCourse(title=course_name, course_code=(course_id or course_name.replace(' ', '_').upper()), academic_year="2024-25", semester=1, description=f"Auto-created for {course_name}")
        db.add(course)
        db.flush()
        return course
    return None

# Few-shot examples for situated learning
FEW_SHOT_EXAMPLES = [
    {
        "domain": "Embedded Systems",
        "topic": "Real-time Processing & Hardware Integration",
        "example": """**Example 1 – Embedded Systems (Real-time Processing & Hardware Integration):**

Problem Statement:
Within your current professional environment, identify a project or system that involves real-time processing, hardware-software integration, or embedded control mechanisms. This could range from IoT device management, industrial automation systems, automotive control units, or telecommunications infrastructure that aligns with embedded systems concepts.

Tasks:
1. **System Analysis & Selection**: Document your chosen workplace system, analyzing its real-time requirements, hardware constraints, and current implementation approach
2. **Architecture Design**: Propose an embedded solution using ARM SoC for high-level control and FPGA for hardware acceleration, incorporating your workplace-specific requirements
3. **Implementation Planning**: Design the software architecture in C/C++, define communication protocols, and specify hardware interfaces (AXI, SPI, I2C) based on your system needs
4. **Validation Strategy**: Develop testing procedures and simulation approaches to validate your proposed solution against workplace performance criteria

Deliverables:
- Technical analysis report of your selected workplace system
- Detailed design document with architecture diagrams and implementation specifications  
- Prototype code samples and hardware configuration files
- Testing plan and validation results demonstrating system performance"""
    },
    {
        "domain": "Mechanical System Design",
        "topic": "Optimization & Analysis",
        "example": """**Example 2 – Mechanical System Design (Optimization & Analysis):**

Problem Statement:
In your current work environment, identify a mechanical system or component that could benefit from design optimization, performance analysis, or efficiency improvements. This might include HVAC systems, manufacturing equipment, automotive components, or industrial machinery that connects with mechanical design principles.

Tasks:
1. **System Identification**: Select and document a relevant mechanical system from your workplace, outlining current performance metrics and optimization opportunities
2. **Data Collection & Modeling**: Gather operational data (workplace data preferred, or reliable online sources with attribution) and develop mathematical models of system behavior
3. **Statistical Analysis**: Apply statistical methods to analyze performance variability, reliability patterns, and identify optimization parameters
4. **Design Optimization**: Implement optimization techniques to enhance efficiency, reduce costs, or improve performance based on your workplace constraints

Deliverables:
- System analysis report with current state assessment and improvement opportunities
- Mathematical models and statistical analysis of system performance
- Optimization recommendations with supporting calculations and simulations
- Implementation plan adapted to your specific workplace context and constraints"""
    },
    {
        "domain": "Software Development",
        "topic": "Object-Oriented Systems & Database Integration",
        "example": """**Example 3 – Software Development (Object-Oriented Systems & Database Integration):**

Problem Statement:
Within your current professional role, identify a software system, application, or data management challenge that could benefit from object-oriented design principles and database optimization. This could involve enterprise applications, web services, mobile apps, or data processing systems currently used in your workplace.

Tasks:
1. **Requirements Analysis**: Document a relevant software challenge from your work environment, analyzing current system limitations and identifying areas where OOP principles and database management could provide improvements
2. **System Design**: Create an object-oriented architecture design that addresses your workplace requirements, incorporating appropriate design patterns, class hierarchies, and database schema optimization
3. **Implementation**: Develop key components of your system using industry-standard programming languages and database management systems relevant to your workplace technology stack
4. **Testing & Performance**: Implement comprehensive testing strategies and database performance optimization techniques, measuring improvements against your workplace success criteria

Deliverables:
- Requirements document and current system analysis based on your workplace context
- Complete system design with UML diagrams, database schema, and architecture documentation
- Working code implementation with proper OOP structure and database integration
- Testing results and performance metrics demonstrating system improvements and workplace applicability"""
    }
]

@router.post("/questions/generate", response_model=QuestionSetResponse)
async def generate_questions(req: QuestionGenerationRequest, db: Session = Depends(get_db)):
    try:
        if not req.student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Use LLMService to generate questions
        llm = LLMService()
        topics = req.topics or []
        
        # Initialize combined text
        all_assignments = []

        selected_examples = select_few_shot_examples(req.domain, req.topics)
        
        # Generate 6 moderate difficulty assignments
        for i in range(6):
            text = await llm.generate_assignment(
                course_name=req.course_name ,
                topics=topics,
                domains=[req.domain],
                difficulty_level="Moderate",
                few_shot_examples=selected_examples,
                custom_instructions=f"""Service/Product Category: {req.service_category or 'N/A'}
                Department: {req.department or 'N/A'}
                Handouts: {', '.join(req.handouts or [])}
                Additional Instructions: Generate a {i+1}/6 unique assignment with clear task description, 
                focusing on practical application in the specified domain.""",
            )
            all_assignments.append(text)
        
        # Each generated text is a complete assignment, add them directly
        questions = []
        for assignment_text in all_assignments:
            # Clean up the text
            cleaned_text = assignment_text
            # .strip().replace('\n', ' ').replace('  ', ' ')
            if len(cleaned_text) > 20:  # Basic validation check
                questions.append(cleaned_text)
        
        # Ensure we have exactly 6 assignments
        questions = questions[:6]

        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate questions")

        course = _find_or_create_course(db, req.course_name, req.course_id)

        row = DBStudentQuestionSet(
            id=uuid4(),
            course_id=course.id if course else None,
            student_id=req.student_id,
            domain=req.domain,
            service_category=req.service_category,
            department=req.department,
            contextual_inputs={"handouts": req.handouts or [], "topics": topics, "custom_instructions": req.custom_instructions},
            generated_questions=questions,
            approval_status='pending'
        )
        db.add(row)
        db.commit()

        return QuestionSetResponse(
            id=str(row.id),
            student_id=row.student_id,
            course_id=str(row.course_id) if row.course_id else None,
            domain=row.domain,
            service_category=row.service_category,
            department=row.department,
            generated_questions=row.generated_questions,
            selected_question=row.selected_question,
            approval_status=row.approval_status,
            created_at=row.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/questions/{question_set_id}/select", response_model=QuestionSetResponse)
async def select_question(question_set_id: str, req: QuestionSelectionRequest, db: Session = Depends(get_db)):
    try:
        row = db.query(DBStudentQuestionSet).filter(DBStudentQuestionSet.id == UUID(question_set_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Question set not found")
        if req.selected_question not in (row.generated_questions or []):
            raise HTTPException(status_code=400, detail="Selected question must be from generated set")
        row.selected_question = req.selected_question
        row.approval_status = 'pending'
        db.commit()
        return QuestionSetResponse(
            id=str(row.id),
            student_id=row.student_id,
            course_id=str(row.course_id) if row.course_id else None,
            course_name=row.course_name,
            domain=row.domain,
            service_category=row.service_category,
            department=row.department,
            generated_questions=row.generated_questions,
            selected_question=row.selected_question,
            approval_status=row.approval_status,
            created_at=row.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{question_set_id}/status", response_model=QuestionSetResponse)
async def get_question_status(question_set_id: str, db: Session = Depends(get_db)):
    try:
        # Get the question set with its latest status
        row = db.query(DBStudentQuestionSet).filter(
            DBStudentQuestionSet.id == UUID(question_set_id)
        ).first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question set not found")
        
        # Return the current status
        return QuestionSetResponse(
            id=str(row.id),
            student_id=row.student_id,
            course_id=str(row.course_id) if row.course_id else None,
            domain=row.domain,
            service_category=row.service_category,
            department=row.department,
            generated_questions=row.generated_questions,
            selected_question=row.selected_question,
            approval_status=row.approval_status,
            faculty_remarks=row.faculty_remarks,
            created_at=row.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AICheckResponse(BaseModel):
    originality_score: float
    ai_detection_score: float
    strengths: List[str]
    improvements: List[str]


@router.post("/ai-check/{submission_id}", response_model=AICheckResponse)
async def ai_check_submission(submission_id: str, db: Session = Depends(get_db)):
    """
    TODO: Implement AI-based checks for student submissions
    - Add AI content detection using advanced LLM
    - Implement plagiarism detection system
    - Add originality scoring
    - Integrate with evaluation service for detailed feedback
    """
    # Temporary placeholder response
    return AICheckResponse(
        originality_score=0.85,  # TODO: Implement actual originality detection
        ai_detection_score=0.15,  # TODO: Implement AI content detection
        strengths=["Clear writing structure", "Relevant industry context"],  # TODO: Extract from actual evaluation
        improvements=["Add more evidence", "Expand analysis"]  # TODO: Generate from detailed assessment
    )

def select_few_shot_examples(domains: List[str], topics: List[str]) -> List[Dict]:
    """Select 3 most relevant few-shot examples based on domains and topics"""
    # Simple matching logic - can be enhanced with semantic similarity
    selected = []
    
    # First, try to match by domain
    for example in FEW_SHOT_EXAMPLES:
        if any(domain.lower() in example["domain"].lower() for domain in domains):
            selected.append(example)
            if len(selected) >= 3:
                break
    
    # If we don't have 3 examples, add remaining ones
    if len(selected) < 3:
        for example in FEW_SHOT_EXAMPLES:
            if example not in selected:
                selected.append(example)
                if len(selected) >= 3:
                    break
    
    return selected[:3]



