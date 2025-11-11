# """
# Student assignment saving endpoint implementation
# """
# import uuid
# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session
# from database.repository import get_db
# from database.models import StudentSubmission, StudentQuestionSet

# def save_student_assignment(
#     data: SaveStudentSubmissionRequest,
#     db: Session
# ) -> dict:
#     """
#     Save a student's approved assignment
#     """
#     # Verify question set exists and is approved
#     try:
#         question_set = db.query(StudentQuestionSet).filter_by(
#             id=uuid.UUID(data.question_set_id)
#         ).first()
        
#         if not question_set:
#             raise HTTPException(status_code=404, detail="Question set not found")
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid question set ID format")
        
#     if question_set.approval_status != 'approved':
#         raise HTTPException(
#             status_code=400, 
#             detail="Cannot save: Assignment must be approved first"
#         )

#     # Create submission record
#     submission = StudentSubmission(
#         id=uuid.uuid4(),
#         student_id=data.student_id,
#         course_id=uuid.UUID(data.course_id) if data.course_id else None,
#         question_set_id=uuid.UUID(data.question_set_id),
#         assignment_text=data.assignment_text,
#         processing_status='saved'
#     )
    
#     db.add(submission)
#     try:
#         db.commit()
#         db.refresh(submission)
#         return {
#             "message": "Assignment saved successfully",
#             "submission_id": str(submission.id)
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Failed to save assignment: {str(e)}"
#         )