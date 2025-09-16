"""
OCR Service for handwritten text extraction
Adapted from llm-based-ocr repository
"""

import base64
import requests
import tempfile
import os
import logging
from typing import List, Optional, Dict, Any
import fitz  # PyMuPDF
from pathlib import Path
from config.settings import settings
from utils.llm_config import llm_config

logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from handwritten or scanned documents using vLLM vision models"""
    
    def __init__(self, image_dpi: int = 200):
        """
        Initialize OCR service using centralized LLM configuration
        
        Args:
            image_dpi: DPI for PDF to image conversion
        """
        # Use centralized LLM configuration for vision model
        self.vllm_api_url = llm_config.vision_model_url
        self.model_name = llm_config.vision_model_name
        self.image_dpi = image_dpi
        self.transcribe_prompt = "Transcribe the handwritten text in this assignment page into plain text. Preserve the structure and formatting as much as possible."
        
        logger.info(f"OCR service initialized with {llm_config.get_config_info()['provider']} vision model: {self.model_name} at {self.vllm_api_url}")
        
    def is_handwritten_content(self, file_path: str) -> bool:
        """
        Determine if content is likely handwritten/scanned vs typed text
        This is a simplified heuristic - could be enhanced with ML models
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if likely handwritten, False if typed text
        """
        try:
            doc = fitz.open(file_path)
            
            # Check if document has extractable text
            total_text_length = 0
            total_pages = len(doc)
            
            for page_num in range(min(3, total_pages)):  # Check first 3 pages
                page = doc.load_page(page_num)
                text = page.get_text()
                total_text_length += len(text.strip())
            
            doc.close()
            
            # Heuristic: If very little extractable text, likely handwritten/scanned
            avg_text_per_page = total_text_length / min(3, total_pages) if total_pages > 0 else 0
            
            # If less than 100 characters per page on average, likely handwritten
            is_handwritten = avg_text_per_page < 100
            
            logger.info(f"Content analysis for {file_path}: avg_text_per_page={avg_text_per_page}, is_handwritten={is_handwritten}")
            return is_handwritten
            
        except Exception as e:
            logger.error(f"Error analyzing content type for {file_path}: {e}")
            # Default to handwritten if we can't determine
            return True
    
    def pdf_to_images(self, pdf_bytes: bytes) -> List[str]:
        """
        Convert PDF bytes to base64 encoded images
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            List of base64 encoded PNG images
        """
        try:
            logger.info(f"Converting PDF to images (DPI: {self.image_dpi})")
            doc = fitz.open(stream=pdf_bytes)
            images = []
            
            for i in range(len(doc)):
                logger.info(f"Processing page {i+1}/{len(doc)}")
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=self.image_dpi)
                img_data = pix.tobytes("png")
                img_b64 = base64.b64encode(img_data).decode("utf-8")
                images.append(img_b64)
                logger.info(f"Page {i+1} converted, image size: {len(img_b64)} characters")
            
            doc.close()
            logger.info(f"Successfully converted {len(images)} pages")
            return images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise
    
    def transcribe_page(self, img_b64: str, page_num: int) -> str:
        """
        Send image to vLLM for transcription
        
        Args:
            img_b64: Base64 encoded image
            page_num: Page number for logging
            
        Returns:
            Transcribed text
        """
        logger.info(f"Transcribing page {page_num} (image size: {len(img_b64)} chars)")
        
        payload = {
            "model": self.model_name,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": self.transcribe_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }]
        }
        
        try:
            logger.info(f"Sending request to vision model at {self.vllm_api_url}")
            
            # Use proper headers from llm_config (includes API key for OpenAI)
            headers = llm_config.get_headers()
            
            response = requests.post(
                self.vllm_api_url, 
                json=payload, 
                timeout=None,  # Allow long processing times for OCR
                headers=headers
            )
            
            logger.info(f"Vision model response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Vision model API error: {response.status_code} - {response.text}")
                raise Exception(f"Vision model API returned {response.status_code}: {response.text}")
            
            response_data = response.json()
            logger.info("Successfully received response from vision model")
            
            # Check if response has expected structure
            if "choices" not in response_data or not response_data["choices"]:
                logger.error(f"Unexpected vision model response format: {response_data}")
                raise Exception("Invalid response format from vision model")
            
            content = response_data["choices"][0]["message"]["content"].strip()
            logger.info(f"Transcribed text length: {len(content)} characters")
            return content
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to vision model API at {self.vllm_api_url}")
            raise Exception(f"Cannot connect to vision model API at {self.vllm_api_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe entire PDF document
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with transcription results
        """
        logger.info(f"Starting OCR transcription for: {file_path}")
        
        try:
            # Read PDF content
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            
            if len(pdf_content) == 0:
                raise Exception("PDF file is empty")
            
            # Convert to images
            images = self.pdf_to_images(pdf_content)
            
            if not images:
                raise Exception("Could not extract any pages from PDF")
            
            # Transcribe each page
            pages = []
            total_text = ""
            confidence_scores = []
            
            for idx, img_b64 in enumerate(images, 1):
                logger.info(f"Transcribing page {idx}/{len(images)}")
                try:
                    text = self.transcribe_page(img_b64, idx)
                    pages.append({
                        "page": idx,
                        "text": text,
                        "status": "success"
                    })
                    total_text += f"\n\n--- Page {idx} ---\n{text}"
                    confidence_scores.append(0.85)  # Placeholder confidence score
                    logger.info(f"Successfully transcribed page {idx}")
                    
                except Exception as e:
                    logger.error(f"Failed to transcribe page {idx}: {str(e)}")
                    error_text = f"[ERROR: Failed to transcribe page {idx} - {str(e)}]"
                    pages.append({
                        "page": idx,
                        "text": error_text,
                        "status": "error",
                        "error": str(e)
                    })
                    total_text += f"\n\n--- Page {idx} ---\n{error_text}"
                    confidence_scores.append(0.0)
            
            # Calculate overall confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            result = {
                "filename": Path(file_path).name,
                "total_pages": len(pages),
                "pages": pages,
                "full_text": total_text.strip(),
                "ocr_confidence": round(avg_confidence, 2),
                "processing_method": "ocr_vision_llm"
            }
            
            logger.info(f"Successfully processed {file_path} with {len(pages)} pages, confidence: {avg_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def extract_text_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Extract text from PDF bytes using OCR
        
        Args:
            pdf_bytes: PDF content as bytes
            filename: Original filename for reference
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Save bytes to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Process the temporary file
                result = self.transcribe_pdf(temp_file_path)
                result["filename"] = filename
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing PDF bytes: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to vLLM vision API
        
        Returns:
            Status dictionary
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [{
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello, can you respond with 'OCR service test successful'?"}]
                }]
            }
            
            # Use proper headers from llm_config (includes API key for OpenAI)
            headers = llm_config.get_headers()
            
            response = requests.post(
                self.vllm_api_url, 
                json=payload, 
                timeout=30,
                headers=headers
            )
            
            if response.status_code == 200:
                return {"status": "success", "message": "OCR service connection successful"}
            else:
                return {"status": "error", "message": f"API returned {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}
