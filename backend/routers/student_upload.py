"""
Student PDF submission processing endpoint
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from uuid import uuid4

from database.repository import get_db
from database.models import StudentSubmission as DBStudentSubmission
from services.submission_processor import SubmissionProcessingService
from storage.minio_client import minio_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize submission processing service
submission_processor = SubmissionProcessingService()

@router.post("/upload-submission")
async def upload_student_submission(
    assignment_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Handle PDF/DOCX file upload for student submission
    Process the file and extract text content
    """
    try:
        if len(files) > 1:
            raise HTTPException(status_code=400, detail="Only one file can be uploaded at a time")

        file = files[0]
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        # Process file and extract text
        file_content = await file.read()
        file_path = f"submissions/{uuid4()}/{file.filename}"
        
        # Upload to MinIO
        minio_client.put_object(
            bucket_name="submissions",
            object_name=file_path,
            data=file_content,
            length=len(file_content)
        )

        # Extract text from file
        extracted_text = await submission_processor.process_file(
            file_content,
            file.filename,
            file.content_type
        )

        # Create submission record
        submission = DBStudentSubmission(
            id=str(uuid4()),
            assignment_id=assignment_id,
            file_path=file_path,
            file_type=file.content_type,
            file_size=len(file_content),
            content=extracted_text,
            evaluation_status="draft"
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)

        return {
            "submission_id": str(submission.id),
            "content": extracted_text,
            "file_name": file.filename,
            "file_size": len(file_content)
        }

    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")