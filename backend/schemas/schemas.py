from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

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


# 🆕 New model for DB insertion only
class SubmissionCreate(BaseModel):
    student_id: str
    assignment_id: str
    content: str
    evaluation_status: Optional[str] = "draft"


# 🆕 Student Submission Response Schema
class StudentSubmissionResponse(BaseModel):
    id: str
    student_id: str
    assignment_id: str
    content: str
    submission_date: datetime
    evaluation_status: str  # draft, pending_faculty, evaluated
    evaluation_score: Optional[float] = None
    
    class Config:
        from_attributes = True


# 🆕 Faculty Evaluation Request Schema
class EvaluationRequest(BaseModel):
    submission_id: str
    criteria_scores: Dict[str, float]
    feedback: str
    faculty_id: Optional[str]="f20220162"

# 🆕 Faculty Evaluation Response Schema
class FacultyEvaluationResponse(BaseModel):
    id: str
    submission_id: str
    rubric_scores: dict
    comments: str
    evaluation_date: datetime
    
    class Config:
        from_attributes = True

class AutoEvaluateRequest(BaseModel):
    faculty_id: Optional[str]=None  # sent from frontend when faculty initiates evaluation

class CriterionFeedback(BaseModel):
    category: str
    score: float
    percentage: float
    feedback: str

class AutoEvaluateResponse(BaseModel):
    submission_id: str
    status: str
    overall_score: float
    overall_feedback: str
    criterion_feedback: List[CriterionFeedback]
    processing_time: float
    llm_model: str
    duration: float