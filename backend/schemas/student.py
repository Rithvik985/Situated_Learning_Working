"""
Student schema models for request/response validation
"""
from typing import Optional, List
from pydantic import BaseModel

class SaveAssignmentRequest(BaseModel):
    """Schema for saving student's selected assignment"""
    question_set_id: str
    student_id: str
    assignment_name: str
    course_name:str