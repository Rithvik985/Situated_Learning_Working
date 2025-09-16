"""
Enhanced Document Processing Service for Student Submission Evaluation
Orchestrates text extraction, OCR processing, and evaluation workflow
"""

import os
import logging
import tempfile
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import asyncio

from .text_extraction_service import TextExtractionService
from .ocr_service import OCRService
from .evaluation_service import EvaluationService, SubmissionEvaluation

logger = logging.getLogger(__name__)

class SubmissionProcessingService:
    """
    Comprehensive service for processing student submissions through the complete evaluation pipeline
    """
    
    def __init__(self):
        """Initialize all required services"""
        self.text_extraction_service = TextExtractionService()
        self.ocr_service = OCRService()
        self.evaluation_service = EvaluationService()
        
        logger.info("Submission Processing Service initialized with all sub-services")
    
    def process_submission_file(self, file_path: str, submission_id: str) -> Dict[str, Any]:
        """
        Process a single submission file to extract text
        
        Args:
            file_path: Path to the submission file
            submission_id: Unique identifier for the submission
            
        Returns:
            Dictionary with extracted text and processing metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing submission file: {file_path} (ID: {submission_id})")
            
            # Extract text using appropriate method
            extraction_result = self.text_extraction_service.extract_text(file_path)
            
            # Add submission metadata
            processing_result = {
                "submission_id": submission_id,
                "extracted_text": extraction_result["text"],
                "extraction_method": extraction_result["extraction_method"],
                "confidence": extraction_result.get("confidence", 0.0),
                "file_info": {
                    "filename": extraction_result["filename"],
                    "file_type": extraction_result["file_type"],
                    "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                },
                "processing_time": time.time() - start_time,
                "status": "success"
            }
            
            # Add additional metadata based on extraction method
            if "ocr_details" in extraction_result:
                processing_result["ocr_details"] = extraction_result["ocr_details"]
            
            if "warning" in extraction_result:
                processing_result["warnings"] = [extraction_result["warning"]]
            
            logger.info(f"Successfully processed {file_path} in {processing_result['processing_time']:.2f}s")
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing submission file {file_path}: {str(e)}")
            return {
                "submission_id": submission_id,
                "status": "error",
                "error_message": str(e),
                "processing_time": time.time() - start_time
            }
    
    def process_submission_bytes(self, file_bytes: bytes, filename: str, submission_id: str) -> Dict[str, Any]:
        """
        Process submission from bytes (for uploaded files)
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            submission_id: Unique identifier for the submission
            
        Returns:
            Dictionary with extracted text and processing metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing submission bytes: {filename} (ID: {submission_id})")
            
            # Determine file type
            file_extension = Path(filename).suffix.lower()
            file_type = file_extension.lstrip('.')
            
            if file_type not in ['pdf', 'docx']:
                raise Exception(f"Unsupported file type: {file_type}")
            
            # Extract text using appropriate method
            extraction_result = self.text_extraction_service.extract_text_from_bytes(
                file_bytes, filename, file_type
            )
            
            # Add submission metadata
            processing_result = {
                "submission_id": submission_id,
                "extracted_text": extraction_result["text"],
                "extraction_method": extraction_result["extraction_method"],
                "confidence": extraction_result.get("confidence", 0.0),
                "file_info": {
                    "filename": filename,
                    "file_type": file_type,
                    "file_size": len(file_bytes)
                },
                "processing_time": time.time() - start_time,
                "status": "success"
            }
            
            # Add additional metadata
            if "ocr_details" in extraction_result:
                processing_result["ocr_details"] = extraction_result["ocr_details"]
            
            if "warning" in extraction_result:
                processing_result["warnings"] = [extraction_result["warning"]]
            
            logger.info(f"Successfully processed {filename} in {processing_result['processing_time']:.2f}s")
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing submission bytes {filename}: {str(e)}")
            return {
                "submission_id": submission_id,
                "status": "error",
                "error_message": str(e),
                "processing_time": time.time() - start_time
            }
    
    def evaluate_submission(self, submission_text: str, assignment_description: str, 
                          rubric: Dict[str, Any], submission_id: str) -> SubmissionEvaluation:
        """
        Evaluate a processed submission against a rubric
        
        Args:
            submission_text: Extracted text from student submission
            assignment_description: Assignment requirements and context
            rubric: Structured rubric for evaluation
            submission_id: Unique identifier for the submission
            
        Returns:
            Complete evaluation result
        """
        try:
            logger.info(f"Evaluating submission {submission_id} against rubric")
            
            # Use evaluation service to score the submission
            evaluation = self.evaluation_service.evaluate_submission(
                assignment_description=assignment_description,
                submission_text=submission_text,
                rubric=rubric,
                submission_id=submission_id
            )
            
            logger.info(f"Evaluation completed for submission {submission_id}: {evaluation.overall_score}/20 ({(evaluation.overall_score/20)*100:.1f}%)")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating submission {submission_id}: {str(e)}")
            raise Exception(f"Evaluation failed: {str(e)}")
    
    def process_and_evaluate_submission(self, file_bytes: bytes, filename: str, 
                                      submission_id: str, assignment_description: str, 
                                      rubric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete pipeline: process file and evaluate against rubric
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            submission_id: Unique identifier
            assignment_description: Assignment context
            rubric: Evaluation rubric
            
        Returns:
            Complete processing and evaluation result
        """
        total_start_time = time.time()
        
        try:
            logger.info(f"Starting complete pipeline for submission {submission_id}")
            
            # Step 1: Process the file to extract text
            processing_result = self.process_submission_bytes(file_bytes, filename, submission_id)
            
            if processing_result["status"] != "success":
                return {
                    "submission_id": submission_id,
                    "status": "processing_failed",
                    "error": processing_result.get("error_message", "Unknown processing error"),
                    "total_time": time.time() - total_start_time
                }
            
            # Step 2: Evaluate the extracted text
            evaluation = self.evaluate_submission(
                submission_text=processing_result["extracted_text"],
                assignment_description=assignment_description,
                rubric=rubric,
                submission_id=submission_id
            )
            
            # Step 3: Combine results
            complete_result = {
                "submission_id": submission_id,
                "status": "success",
                "processing": processing_result,
                "evaluation": {
                    "overall_score": evaluation.overall_score,
                    "total_questions": evaluation.total_questions,
                    "percentage": (evaluation.overall_score / 20) * 100,
                    "criterion_evaluations": [
                        {
                            "category": ce.category,
                            "score": ce.score,
                            "max_score": ce.max_score,
                            "percentage": ce.percentage,
                            "feedback": ce.feedback,
                            "question_results": [
                                {
                                    "category": q.category,
                                    "question": q.question,
                                    "score": q.score,
                                    "reasoning": q.reasoning
                                }
                                for q in ce.question_results
                            ]
                        }
                        for ce in evaluation.criterion_evaluations
                    ],
                    "overall_feedback": evaluation.overall_feedback,
                    "evaluation_metadata": evaluation.evaluation_metadata,
                    "processing_time": evaluation.processing_time
                },
                "total_time": time.time() - total_start_time
            }
            
            logger.info(f"Complete pipeline finished for submission {submission_id} in {complete_result['total_time']:.2f}s")
            return complete_result
            
        except Exception as e:
            logger.error(f"Error in complete pipeline for submission {submission_id}: {str(e)}")
            return {
                "submission_id": submission_id,
                "status": "pipeline_failed",
                "error": str(e),
                "total_time": time.time() - total_start_time
            }
    
    def process_multiple_submissions(self, submissions: List[Dict[str, Any]], 
                                   assignment_description: str, rubric: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process multiple submissions in batch
        
        Args:
            submissions: List of submission dictionaries with file_bytes, filename, submission_id
            assignment_description: Assignment context
            rubric: Evaluation rubric
            
        Returns:
            List of processing and evaluation results
        """
        results = []
        total_start_time = time.time()
        
        logger.info(f"Processing batch of {len(submissions)} submissions")
        
        for i, submission in enumerate(submissions, 1):
            logger.info(f"Processing submission {i}/{len(submissions)}: {submission.get('filename', 'unknown')}")
            
            try:
                result = self.process_and_evaluate_submission(
                    file_bytes=submission["file_bytes"],
                    filename=submission["filename"],
                    submission_id=submission["submission_id"],
                    assignment_description=assignment_description,
                    rubric=rubric
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing submission {submission.get('submission_id', 'unknown')}: {str(e)}")
                results.append({
                    "submission_id": submission.get("submission_id", f"unknown_{i}"),
                    "status": "failed",
                    "error": str(e),
                    "filename": submission.get("filename", "unknown")
                })
        
        total_time = time.time() - total_start_time
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all sub-services
        
        Returns:
            Status dictionary for all services
        """
        try:
            # Test OCR service
            ocr_status = self.ocr_service.test_connection()
            
            # Test evaluation service
            eval_status = self.evaluation_service.test_connection()
            
            return {
                "submission_processor": {"status": "active"},
                "text_extraction": {"status": "active"},
                "ocr_service": ocr_status,
                "evaluation_service": eval_status,
                "overall_status": "healthy" if (
                    ocr_status["status"] == "success" and eval_status["status"] == "success"
                ) else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Error checking service status: {str(e)}")
            return {
                "submission_processor": {"status": "error", "error": str(e)},
                "overall_status": "unhealthy"
            }
