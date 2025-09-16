"""
Image analysis service for analyzing images in PDFs using Vision LLM
"""
import os
import io
import base64
import openai
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageStat
from typing import List, Dict, Any, Optional
from io import BytesIO
from config.settings import settings
from utils.llm_config import llm_config

# Image processing settings
IMAGE_MIN_SIZE = 70
IMAGE_MAX_SIZE = 2000
IMAGE_OVERLAP_THRESHOLD = 20

# OpenAI client will be initialized lazily when needed
client = None

def get_openai_client():
    """Get or create OpenAI client instance using centralized LLM configuration"""
    global client
    if client is None:
        # Use centralized LLM configuration for vision model
        base_url = llm_config.vision_model_url.replace('/chat/completions', '')
        model_name = llm_config.vision_model_name
        
        # For vision models, we typically use local vLLM, so use dummy API key
        api_key = "dummy-key"
        
        print("[DEBUG] Vision LLM Configuration:")
        print(f"[DEBUG] Base URL: {base_url}")
        print(f"[DEBUG] Model: {model_name}")
        print(f"[DEBUG] Provider: {llm_config.get_config_info()['provider']}")
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    return client

def _is_image_in_visible_area(page, xref: int, img_num: int) -> bool:
    """Check if an image is within the visible area of the partitioned PDF page"""
    try:
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        try:
            image_rects = page.get_image_rects(xref)
            if not image_rects:
                return False
            
            for rect in image_rects:
                rect_x0, rect_y0, rect_x1, rect_y1 = rect
                
                if (rect_x1 > 0 and rect_x0 < page_width and 
                    rect_y1 > 0 and rect_y0 < page_height):
                    
                    overlap_x0 = max(0, rect_x0)
                    overlap_y0 = max(0, rect_y0)
                    overlap_x1 = min(page_width, rect_x1)
                    overlap_y1 = min(page_height, rect_y1)
                    
                    overlap_width = max(0, overlap_x1 - overlap_x0)
                    overlap_height = max(0, overlap_y1 - overlap_y0)
                    overlap_area = overlap_width * overlap_height
                    
                    rect_width = rect_x1 - rect_x0
                    rect_height = rect_y1 - rect_y0
                    rect_area = rect_width * rect_height
                    
                    if rect_area > 0:
                        overlap_percentage = (overlap_area / rect_area) * 100
                        if overlap_percentage > IMAGE_OVERLAP_THRESHOLD:
                            return True
            
            return False
            
        except Exception:
            return True
            
    except Exception:
        return True

def _extract_image_with_fallbacks(page, xref: int, img_num: int) -> Optional[dict]:
    """Extract image using multiple fallback methods"""
    try:
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        image = Image.open(BytesIO(image_bytes))
        
        if image.size[0] > 0 and image.size[1] > 0:
            return {'image': image, 'method': 'standard_extraction', 'colorspace': base_image.get('colorspace', 'unknown')}
    except Exception:
        pass
    
    try:
        base_image = page.parent.extract_image(xref, keep_alpha=False)
        image_bytes = base_image["image"]
        image = Image.open(BytesIO(image_bytes))
        
        if image.size[0] > 0 and image.size[1] > 0:
            return {'image': image, 'method': 'no_alpha_extraction', 'colorspace': base_image.get('colorspace', 'unknown')}
    except Exception:
        pass
    
    try:
        mat = fitz.Matrix(2.0, 2.0)
        pixmap = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pixmap.tobytes("png")
        image = Image.open(BytesIO(img_data))
        
        if image.size[0] > 0 and image.size[1] > 0:
            return {'image': image, 'method': 'pixmap_rendering', 'colorspace': 'rendered'}
    except Exception:
        pass
    
    return None

def _apply_color_corrections(image: Image.Image, img_num: int) -> Image.Image:
    """Apply color corrections to fix common PDF extraction issues"""
    try:
        if image.mode != 'RGB':
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode in ['L', 'P', 'CMYK']:
                image = image.convert('RGB')
        
        # Check if image needs contrast adjustment
        stat = ImageStat.Stat(image)
        if len(stat.stddev) == 3:  # RGB
            avg_stddev = sum(stat.stddev) / 3
            if avg_stddev < 20:  # Low contrast
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)  # Subtle enhancement
        
        return image
        
    except Exception:
        return image

def _validate_image_comprehensively(image: Image.Image, img_num: int) -> dict:
    """Comprehensive image validation"""
    width, height = image.size
    
    # Size validation
    if width < IMAGE_MIN_SIZE or height < IMAGE_MIN_SIZE:
        return {'is_valid': False, 'reason': f'TOO_SMALL - {width}x{height}px < {IMAGE_MIN_SIZE}px'}
    
    if width > IMAGE_MAX_SIZE or height > IMAGE_MAX_SIZE:
        return {'is_valid': False, 'reason': f'TOO_LARGE - {width}x{height}px > {IMAGE_MAX_SIZE}px'}
    
    # Format validation
    if image.mode not in ['RGB', 'RGBA', 'L', 'P']:
        return {'is_valid': False, 'reason': f'UNSUPPORTED_FORMAT - {image.mode}'}
    
    # Content richness check
    stat = ImageStat.Stat(image)
    if len(stat.stddev) == 3:  # RGB
        avg_stddev = sum(stat.stddev) / 3
        if avg_stddev < 8:  # Very low variation
            return {'is_valid': False, 'reason': f'LOW_VARIATION - {avg_stddev:.1f}'}
    
    return {'is_valid': True, 'reason': 'PASSED_ALL_CHECKS'}

def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = BytesIO()
    
    # Ensure RGB mode
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save as PNG for best quality
    image.save(buffered, format="PNG", optimize=True)
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_base64

def describe_educational_image_with_base64(base64_image: str) -> str:
    """Get image description from Vision LLM using centralized configuration"""
    try:
        # Use centralized LLM configuration for vision model
        model_name = llm_config.vision_model_name
        
        print(f"[DEBUG] Calling Vision LLM with model: {model_name}")
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at analyzing educational content images. "
                        "Provide clear, structured descriptions that capture essential educational elements. "
                        "Focus on mathematical formulas, diagrams, charts, graphs, illustrations, and text content. "
                        "If the image is clearly a logo, watermark, header/footer, or purely decorative element with no educational value, "
                        "respond with exactly 'DECORATIVE_ELEMENT'. "
                        "For meaningful content, be concise but comprehensive."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this image and provide a structured description focusing on educational content:\n"
                                "- Content type: [mathematical formula/diagram/chart/graph/illustration/text/etc.]\n"
                                "- Key elements: [main components, labels, values]\n"
                                "- Educational purpose: [what concept it teaches or demonstrates]\n"
                                "- Important details: [formulas, relationships, data points, include object positions, shapes, sizes, label names, arrows, styles, fonts, spacing, and any implied relationships.]\n\n"
                                "Keep it concise and relevant to learning. "
                                "Only respond with 'DECORATIVE_ELEMENT' if this has absolutely no educational value."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        print(f"[DEBUG] Vision LLM response received: {len(result) if result else 0} characters")
        return result
    except Exception as e:
        print(f"[ERROR] Error getting image description: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return None

def extract_image_descriptions_from_page(page, pdf_name: str = None, output_dir: str = None) -> List[str]:
    """Extract and analyze images from a PDF page"""
    images = list(page.get_images(full=True))
    print(f"[DEBUG] Found {len(images)} images on page")
    image_descriptions = []
    relevant_image_count = 0
    
    for img_index, img in enumerate(images):
        print(f"[DEBUG] Processing image {img_index + 1}/{len(images)}")
        try:
            xref = img[0]
            
            # Check if image is in visible area
            if not _is_image_in_visible_area(page, xref, img_index + 1):
                print(f"[DEBUG] Image {img_index + 1} not in visible area, skipping")
                continue
            
            # Extract image with fallbacks
            image_data = _extract_image_with_fallbacks(page, xref, img_index + 1)
            if not image_data:
                print(f"[DEBUG] Image {img_index + 1} extraction failed, skipping")
                continue
            
            image = image_data['image']
            print(f"[DEBUG] Image {img_index + 1} extracted successfully, size: {image.size}")
            
            # Apply color corrections
            corrected_image = _apply_color_corrections(image, img_index + 1)
            
            # Validate image
            validation_result = _validate_image_comprehensively(corrected_image, img_index + 1)
            if not validation_result['is_valid']:
                print(f"[DEBUG] Image {img_index + 1} validation failed: {validation_result['reason']}")
                continue
            
            print(f"[DEBUG] Image {img_index + 1} passed validation, calling Vision LLM...")
            
            # Convert to base64
            img_base64 = _image_to_base64(corrected_image)
            
            # Get description from Vision LLM
            description = describe_educational_image_with_base64(img_base64)
            print(f"[DEBUG] Image {img_index + 1} LLM response: {description[:100] if description else 'None'}...")
            
            # Add description if not decorative
            if description and description != "DECORATIVE_ELEMENT":
                relevant_image_count += 1
                
                # Format description
                if relevant_image_count > 1:
                    formatted_description = f"Image {relevant_image_count}: {description}"
                else:
                    formatted_description = f"Image description: {description}"
                
                image_descriptions.append(formatted_description)
                print(f"[DEBUG] Image {img_index + 1} added to descriptions")
            else:
                print(f"[DEBUG] Image {img_index + 1} marked as decorative or no description")
                
        except Exception as e:
            print(f"[ERROR] Error processing image {img_index + 1}: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            continue
    
    print(f"[DEBUG] Total relevant images found: {relevant_image_count}")
    return image_descriptions

def extract_from_pdf(pdf_path: str, output_dir: str = None) -> str:
    """Extract text and image descriptions from a PDF"""
    print(f"[DEBUG] extract_from_pdf called with {pdf_path}")
    text_extract = ""
    pdf_name = os.path.basename(pdf_path)
    
    try:
        with fitz.open(pdf_path) as doc:
            print(f"[DEBUG] PDF opened successfully, {len(doc)} pages")
            for page_num, page in enumerate(doc):
                print(f"[DEBUG] Processing page {page_num + 1}")
                # Extract text
                text = page.get_text()
                print(f"[DEBUG] Extracted {len(text)} characters of text")
                
                # Extract image descriptions
                print(f"[DEBUG] Looking for images on page {page_num + 1}")
                image_descriptions = extract_image_descriptions_from_page(
                    page, 
                    pdf_name=pdf_name, 
                    output_dir=output_dir
                )
                print(f"[DEBUG] Found {len(image_descriptions)} image descriptions")
                
                # Combine text and image descriptions
                page_text = text + "\n"
                if image_descriptions:
                    combined_description = "\n".join(image_descriptions)
                    page_text += f"\n[Image Descriptions]:\n{combined_description}\n"
                    print(f"[DEBUG] Added image descriptions to page text")
                
                # Append to overall text
                if page_num > 0:
                    text_extract += "\n\n" + page_text
                else:
                    text_extract = page_text
                    
    except Exception as e:
        print(f"[ERROR] Error reading PDF {pdf_path}: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        text_extract = f"[Error reading PDF: {str(e)}]"
    
    print(f"[DEBUG] Final extracted content length: {len(text_extract)}")
    return text_extract.strip()
