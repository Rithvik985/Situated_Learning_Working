"""
Document processing service for extracting questions from assignments
"""
import os
import tempfile
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import logging
import re
from datetime import datetime
from .image_analyzer import extract_from_pdf

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing assignment documents and extracting questions"""
    
    def __init__(self):
        self.question_patterns = [
            r'^(\d+)[\.\)]\s*',  # 1. or 1)
            r'^Q\.?\s*(\d+)[\.\):]?\s*',  # Q1. or Q.1 or Q1:
            r'^Question\s*(\d+)[\.\):]?\s*',  # Question 1.
            r'^Problem\s*(\d+)[\.\):]?\s*',  # Problem 1.
            r'^\[(\d+)\]',  # [1]
            r'^Part\s*([A-Z]|\d+)[\.\):]?\s*',  # Part A or Part 1
        ]
    
    def extract_questions_from_pdf(self, pdf_path: str, output_dir: str) -> Tuple[List[Dict], List[str], Dict]:
        """
        Extract questions from PDF and create separate question files
        
        Args:
            pdf_path: Path to the input PDF
            output_dir: Directory to save extracted questions
            
        Returns:
            Tuple of (matches, output_files, metadata)
        """
        try:
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Find question patterns
            all_matches = self._find_question_patterns(doc)
            
            if not all_matches:
                logger.warning(f"No questions found in {pdf_path}")
                doc.close()
                return [], [], {}
            
            # Determine question segments
            question_segments = self._determine_question_segments(all_matches, doc)
            
            # Create output files - EXACTLY like Question_Review_System
            output_files = []
            
            # Create output directory in project temp
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            project_temp_dir = os.path.join(project_root, "temp")
            os.makedirs(project_temp_dir, exist_ok=True)
            
            # Create unique subdirectory for this PDF
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            # Sanitize filename to avoid any path issues
            pdf_name = re.sub(r'[<>:"/\\|?*]', '_', pdf_name)  # Replace invalid characters with underscore
            pdf_name = pdf_name.replace(' ', '_')  # Replace spaces with underscore
            if len(pdf_name) > 50:  # Limit filename length
                pdf_name = pdf_name[:50]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            unique_dir = os.path.join(project_temp_dir, f"questions_{pdf_name}_{timestamp}")
            os.makedirs(unique_dir, exist_ok=True)
            logger.info(f"Created unique output directory: {unique_dir}")
            
            for question in question_segments:
                # Create PDF filename using actual question number
                question_num = question['question_number']
                pdf_filename = f"question_{question_num:02d}.pdf"
                output_path = os.path.join(unique_dir, pdf_filename)
                
                logger.info(f"Creating question PDF: {output_path}")
                logger.info(f"Question {question_num} spans {question['total_pages']} page(s)")
                
                # Create the multi-page PDF
                success = self._create_question_pdf(doc, question['segments'], output_path, question_num)
                
                if success:
                    output_files.append(output_path)
                    logger.info(f"Successfully created question {question_num}")
                    logger.info(f"  Pattern used: {question['pattern_used']}")
                    logger.info(f"  Question starter: {question['starter']}")
                else:
                    logger.error(f"Failed to create question {question_num}")
            
            # Extract basic metadata
            metadata = self._extract_basic_metadata(doc)
            
            doc.close()
            
            logger.info(f"✅ Extracted {len(output_files)} questions from {os.path.basename(pdf_path)}")
            logger.info(f"Output directory: {unique_dir}/")
            logger.info(f"Total questions extracted: {len(output_files)}")
            return all_matches, output_files, metadata
            
        except Exception as e:
            logger.error(f"❌ Error extracting questions from {pdf_path}: {e}")
            raise
    
    def _find_question_patterns(self, doc: fitz.Document) -> List[Dict]:
        """Find question pattern matches in the document - EXACTLY like Question_Review_System"""
        all_matches = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            page_height = page.rect.height
            
            for block in text_dict["blocks"]:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        
                        # Check against all patterns
                        for pattern in self.question_patterns:
                            match = re.match(pattern, text, re.IGNORECASE)
                            if match:
                                # Extract the actual question number from the match
                                question_num = match.group(1)
                                
                                # Store match info
                                all_matches.append({
                                    'page': page_num,
                                    'y_pos': span["bbox"][1],  # Top Y position
                                    'text': text,
                                    'pattern_used': pattern,
                                    'page_height': page_height,
                                    'starter': text,  # Full text that starts the question
                                    'question_number': int(question_num) if question_num.isdigit() else 0
                                })
                                break
        
        # Sort by page and position
        all_matches.sort(key=lambda x: (x['page'], x['y_pos']))
        
        # Validate and log matches
        if all_matches:
            logger.info(f"Found {len(all_matches)} question patterns:")
            for match in all_matches:
                logger.info(f"  Page {match['page'] + 1}, Y: {match['y_pos']:.2f}, Text: {match['starter']}")
        else:
            logger.warning("No question patterns found in document")
        
        return all_matches
    
    def _determine_question_segments(self, all_matches: List[Dict], doc: fitz.Document) -> List[Dict]:
        """Determine how questions span across pages - EXACTLY like Question_Review_System"""
        if not all_matches:
            return []
        
        questions = []
        
        for i, current_match in enumerate(all_matches):
            question_segments = []
            
            # Determine where this question ends
            if i + 1 < len(all_matches):
                next_match = all_matches[i + 1]
                
                # Check if question spans multiple pages
                if current_match['page'] == next_match['page']:
                    # Same page - simple case
                    question_segments.append({
                        'page': current_match['page'],
                        'y_start': max(0, current_match['y_pos'] - 5),  # Small margin above
                        'y_end': next_match['y_pos'] - 2  # Stop just before next question
                    })
                else:
                    # Multi-page question
                    logger.info(f"Multi-page question detected: Q{i+1} spans from page {current_match['page']+1} to page {next_match['page']+1}")
                    
                    # First segment: from current pattern to end of current page
                    question_segments.append({
                        'page': current_match['page'],
                        'y_start': max(0, current_match['y_pos'] - 5),
                        'y_end': current_match['page_height']  # Go to end of page
                    })
                    
                    # Middle segments: any complete pages between start and end
                    for middle_page in range(current_match['page'] + 1, next_match['page']):
                        question_segments.append({
                            'page': middle_page,
                            'y_start': 0,  # Start from top of page
                            'y_end': current_match['page_height']  # Full page height
                        })
                        logger.info(f"  Added full page {middle_page + 1} to question {i+1}")
                    
                    # Last segment: from top of next page to next pattern
                    if next_match['page'] > current_match['page']:
                        question_segments.append({
                            'page': next_match['page'],
                            'y_start': 0,  # Start from top of page
                            'y_end': next_match['y_pos'] - 2  # Stop before next question
                        })
            else:
                # Last question - goes to end of document
                question_segments.append({
                    'page': current_match['page'],
                    'y_start': max(0, current_match['y_pos'] - 5),
                    'y_end': current_match['page_height']
                })
                
                # Add any remaining pages
                for remaining_page in range(current_match['page'] + 1, len(doc)):
                    question_segments.append({
                        'page': remaining_page,
                        'y_start': 0,
                        'y_end': doc[remaining_page].rect.height
                    })
            
            # Store question info
            questions.append({
                'question_number': current_match['question_number'] or (i + 1),
                'starter': current_match['starter'],
                'segments': question_segments,
                'total_pages': len(question_segments),
                'pattern_used': current_match.get('pattern_used', 'unknown')
            })
        
        return questions
    
    def _create_question_pdf(self, source_doc: fitz.Document, segments: List[Dict], 
                           output_path: str, question_num: int) -> bool:
        """Create a PDF containing a question that may span multiple pages"""
        try:
            logger.info(f"Creating question PDF {question_num} with {len(segments)} segments")
            logger.info(f"Output path: {output_path}")
            
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
            
            # Create a new PDF document
            new_doc = fitz.open()
            
            for segment in segments:
                page_num = segment['page']
                y_start = segment['y_start']
                y_end = segment['y_end']
                
                # Get the source page
                source_page = source_doc[page_num]
                page_rect = source_page.rect
                
                # Define the crop rectangle for this segment
                crop_rect = fitz.Rect(
                    0,  # x0 - start from left edge
                    y_start,  # y0 - start Y position
                    page_rect.width,  # x1 - full width
                    min(y_end, page_rect.height)  # y1 - end Y position (don't exceed page)
                )
                
                # Calculate the height of this segment
                segment_height = crop_rect.height
                
                # Create new page for this segment
                new_page = new_doc.new_page(width=crop_rect.width, height=segment_height)
                
                # Copy the cropped area from source to new page
                new_page.show_pdf_page(
                    fitz.Rect(0, 0, crop_rect.width, segment_height),  # target rectangle
                    source_doc,  # source document
                    page_num,  # source page number
                    clip=crop_rect  # area to copy
                )
                
                logger.info(f"  Added segment from page {page_num + 1}, Y {y_start:.2f}-{y_end:.2f} (height: {segment_height:.2f})")
            
            # Save the new PDF
            logger.info(f"Saving PDF to: {output_path}")
            new_doc.save(output_path)
            new_doc.close()
            
            # Verify the file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Created multi-page question PDF: {output_path} (size: {file_size} bytes)")
                logger.info(f"  Question spans {len(segments)} page segment(s)")
                return True
            else:
                logger.error(f"PDF file was not created: {output_path}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating multi-page question PDF {output_path}: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _extract_basic_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract basic metadata from the document"""
        metadata = {
            'page_count': len(doc),
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'creator': doc.metadata.get('creator', ''),
        }
        
        # Try to extract course information from first page
        if len(doc) > 0:
            first_page_text = doc[0].get_text()
            
            # Look for common patterns
            course_patterns = [
                r'Course[:\s]+([^\\n]+)',
                r'Subject[:\s]+([^\\n]+)',
                r'Paper[:\s]+([^\\n]+)',
            ]
            
            for pattern in course_patterns:
                match = re.search(pattern, first_page_text, re.IGNORECASE)
                if match:
                    metadata['extracted_course'] = match.group(1).strip()
                    break
        
        return metadata
    
    def convert_docx_to_pdf(self, docx_path: str, output_dir: str) -> str:
        """
        Convert DOCX file to PDF
        
        Args:
            docx_path: Path to DOCX file
            output_dir: Directory to save PDF
            
        Returns:
            str: Path to converted PDF file
        """
        try:
            import subprocess
            
            # Generate output PDF path
            base_name = os.path.splitext(os.path.basename(docx_path))[0]
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            
            # Try LibreOffice conversion
            try:
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", output_dir,
                    docx_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(pdf_path):
                    logger.info(f"✅ Converted DOCX to PDF using LibreOffice: {pdf_path}")
                    return pdf_path
                else:
                    logger.warning(f"LibreOffice conversion failed: {result.stderr}")
            
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"LibreOffice not available or failed: {e}")
            
            # Fallback: try python-docx2pdf (Windows only)
            try:
                from docx2pdf import convert
                convert(docx_path, pdf_path)
                
                if os.path.exists(pdf_path):
                    logger.info(f"✅ Converted DOCX to PDF using docx2pdf: {pdf_path}")
                    return pdf_path
            
            except ImportError:
                logger.warning("docx2pdf not available")
            except Exception as e:
                logger.warning(f"docx2pdf conversion failed: {e}")
            
            raise Exception("No DOCX to PDF converter available")
            
        except Exception as e:
            logger.error(f"❌ Error converting DOCX to PDF: {e}")
            raise

# Global document processor instance
document_processor = DocumentProcessor()
