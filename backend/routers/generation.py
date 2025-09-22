"""
Assignment generation router with comprehensive functionality
"""

import json
import uuid
import requests
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import GeneratedAssignment as DBGeneratedAssignment, AssignmentRubric as DBAssignmentRubric, Course as DBCourse
from database.repository import get_db
from services.llm_service import LLMService
from services.rubric_service import RubricService
from config.settings import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

def find_or_create_course(db: Session, course_name: str, course_id: Optional[str] = None, academic_year: str = "2024-25", semester: int = 1) -> DBCourse:
    """Find existing course or create a new one based on course_name, course_id, academic_year, and semester"""
    
    # First, try to find by course_code, academic_year, and semester if provided
    if course_id:
        course = db.query(DBCourse).filter(
            DBCourse.course_code == course_id,
            DBCourse.academic_year == academic_year,
            DBCourse.semester == semester
        ).first()
        if course:
            return course
    
    # Try to find by course name, academic_year, and semester
    course = db.query(DBCourse).filter(
        DBCourse.title == course_name,
        DBCourse.academic_year == academic_year,
        DBCourse.semester == semester
    ).first()
    if course:
        return course
    
    # Create a new course if not found
    new_course = DBCourse(
        title=course_name,
        course_code=course_id or course_name.replace(' ', '_').upper(),
        academic_year=academic_year,
        semester=semester,
        description=f"Auto-generated course for {course_name}"
    )
    
    db.add(new_course)
    db.flush()  # Flush to get the ID but don't commit yet
    
    return new_course

# Predefined domains for dropdown
PREDEFINED_DOMAINS = [
    "Semiconductor Industry",
    "Electronics Manufacturing", 
    "Research & Development",
    "Automotive Industry",
    "Consumer Electronics",
    "Industrial Automation",
    "Manufacturing",
    "Aerospace",
    "Healthcare Robotics",
    "Software Development",
    "IT Consulting",
    "FinTech",
    "Internet of Things (IoT)",
    "Human Resource Management",
    "Supply Chain Management",
    "Energy Management",
    "Telecommunications"
]

class AssignmentGenerationRequest(BaseModel):
    course_name: str = Field(..., description="Name of the course")
    course_id: Optional[str] = Field(None, description="Course ID")
    academic_year: str = Field(..., description="Academic year (e.g., 2023-24)")
    semester: int = Field(..., description="Semester number (1 or 2)")
    topics: List[str] = Field(..., description="List of topics (max 4)")
    domains: List[str] = Field(..., description="List of selected domains")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for generation")

class GeneratedAssignmentResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty_level: str
    topics: List[str]
    domains: List[str]
    tags: List[str]
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AssignmentEditRequest(BaseModel):
    title: str
    description: str
    reason_for_change: str = Field(..., description="Mandatory reason for editing")

class RubricGenerationRequest(BaseModel):
    assignment_ids: List[str] = Field(..., description="List of selected assignment IDs")
    rubric_name: Optional[str] = Field(None, description="Custom name for the rubric")

class RubricEditRequest(BaseModel):
    criteria: Dict[str, Any]
    reason_for_edit: str = Field(..., description="Reason for editing the rubric")
    name_only_change: Optional[bool] = Field(False, description="Whether this is only a name/type change")

class SaveAssignmentRequest(BaseModel):
    assignment_name: str = Field(..., description="User-provided name for the assignment")
    selected_assignment_ids: List[str] = Field(..., description="Selected assignment IDs")
    rubric_id: Optional[str] = Field(None, description="Associated rubric ID")

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

@router.get("/domains")
async def get_domains():
    """Get list of predefined domains for the dropdown"""
    return {"domains": PREDEFINED_DOMAINS}

@router.post("/generate")
async def generate_assignments(
    request: AssignmentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate 6 situational assignments across 3 difficulty levels (2 per level)
    """
    try:
        # Validate topics count
        if len(request.topics) > 4:
            raise HTTPException(status_code=400, detail="Maximum 4 topics allowed")
        
        # Validate semester
        if request.semester not in [1, 2]:
            raise HTTPException(status_code=400, detail="Semester must be 1 or 2")
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Find or create the course with academic year and semester
        course = find_or_create_course(db, request.course_name, request.course_id, request.academic_year, request.semester)
        
        # Select appropriate few-shot examples
        selected_examples = select_few_shot_examples(request.domains, request.topics)
        
        # Generate assignments across different difficulty levels
        assignments = []
        difficulty_levels = ["Beginner", "Intermediate", "Advanced"]
        
        for difficulty in difficulty_levels:
            # Generate 2 assignments per difficulty level
            for i in range(2):
                logger.info(f"Generating {difficulty} assignment {i+1}/2...")
                assignment_text = await llm_service.generate_assignment(
                    course_name=request.course_name,
                    topics=request.topics,
                    domains=request.domains,
                    difficulty_level=difficulty,
                    custom_instructions=request.custom_instructions,
                    few_shot_examples=selected_examples
                )
                logger.info(f"✅ Generated {difficulty} assignment {i+1}/2")
                
                # Save to database
                db_assignment = DBGeneratedAssignment(
                    id=uuid.uuid4(),
                    course_name=request.course_name,
                    course_id=course.id,
                    title=extract_title_from_content(assignment_text),
                    description=assignment_text,
                    difficulty_level=difficulty,
                    topics=request.topics,
                    domains=request.domains,
                    custom_instructions=request.custom_instructions,
                    tags=["AI-Generated"]
                )
                
                db.add(db_assignment)
                db.flush()  # This ensures the ID and timestamps are set
                assignments.append(db_assignment)
        
        db.commit()
        logger.info(f"Generated {len(assignments)} assignments for course: {request.course_name}")
        
        # Convert to response models
        response_assignments = []
        for db_assignment in assignments:
            response_assignments.append(GeneratedAssignmentResponse(
                id=str(db_assignment.id),
                title=db_assignment.title,
                description=db_assignment.description,
                difficulty_level=db_assignment.difficulty_level,
                topics=db_assignment.topics,
                domains=db_assignment.domains,
                tags=db_assignment.tags,
                version=db_assignment.version,
                created_at=db_assignment.created_at
            ))
        
        return response_assignments
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate assignments: {str(e)}")

@router.post("/generate-progressive")
async def generate_assignments_progressive(
    request: AssignmentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate assignments progressively using Server-Sent Events
    This allows the frontend to display assignments as they're generated
    """
    async def generate_stream():
        try:
            # Validate topics count
            if len(request.topics) > 4:
                yield f"data: {json.dumps({'error': 'Maximum 4 topics allowed'})}\n\n"
                return
            
            # Validate semester
            if request.semester not in [1, 2]:
                yield f"data: {json.dumps({'error': 'Semester must be 1 or 2'})}\n\n"
                return
            
            # Initialize LLM service
            llm_service = LLMService()
            
            # Find or create the course with academic year and semester
            course = find_or_create_course(db, request.course_name, request.course_id, request.academic_year, request.semester)
            
            # Select appropriate few-shot examples
            selected_examples = select_few_shot_examples(request.domains, request.topics)
            
            # Send initial progress
            yield f"data: {json.dumps({'type': 'progress', 'message': 'Starting assignment generation...', 'total': 6, 'completed': 0})}\n\n"
            
            # Generate assignments across different difficulty levels
            difficulty_levels = ["Beginner", "Intermediate", "Advanced"]
            completed = 0
            
            for difficulty in difficulty_levels:
                # Generate 2 assignments per difficulty level
                for i in range(2):
                    try:
                        logger.info(f"Generating {difficulty} assignment {i+1}/2...")
                        
                        # Send progress update
                        yield f"data: {json.dumps({'type': 'progress', 'message': f'Generating {difficulty} assignment {i+1}/2...', 'total': 6, 'completed': completed})}\n\n"
                        
                        assignment_text = await llm_service.generate_assignment(
                            course_name=request.course_name,
                            topics=request.topics,
                            domains=request.domains,
                            difficulty_level=difficulty,
                            custom_instructions=request.custom_instructions,
                            few_shot_examples=selected_examples
                        )
                        
                        # Save to database
                        db_assignment = DBGeneratedAssignment(
                            id=uuid.uuid4(),
                            course_name=request.course_name,
                            course_id=course.id,
                            title=extract_title_from_content(assignment_text),
                            description=assignment_text,
                            difficulty_level=difficulty,
                            topics=request.topics,
                            domains=request.domains,
                            custom_instructions=request.custom_instructions,
                            tags=["AI-Generated"]
                        )
                        
                        db.add(db_assignment)
                        db.flush()  # This ensures the ID and timestamps are set
                        
                        # Convert to response model
                        try:
                            response_assignment = GeneratedAssignmentResponse(
                                id=str(db_assignment.id),
                                title=db_assignment.title,
                                description=db_assignment.description,
                                difficulty_level=db_assignment.difficulty_level,
                                topics=db_assignment.topics,
                                domains=db_assignment.domains,
                                tags=db_assignment.tags,
                                version=db_assignment.version,
                                created_at=db_assignment.created_at
                            )
                        except Exception as e:
                            logger.error(f"Error creating response model: {str(e)}")
                            logger.error(f"db_assignment.created_at type: {type(db_assignment.created_at)}")
                            logger.error(f"db_assignment.created_at value: {db_assignment.created_at}")
                            raise
                        
                        completed += 1
                        logger.info(f"✅ Generated {difficulty} assignment {i+1}/2")
                        
                        # Send the completed assignment
                        assignment_data = response_assignment.dict()
                        # Convert datetime to string for JSON serialization
                        if 'created_at' in assignment_data and assignment_data['created_at']:
                            assignment_data['created_at'] = assignment_data['created_at'].isoformat()
                        
                        # Ensure all data is JSON serializable
                        def json_serial(obj):
                            if hasattr(obj, 'isoformat'):
                                return obj.isoformat()
                            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                        
                        yield f"data: {json.dumps({'type': 'assignment', 'assignment': assignment_data, 'completed': completed, 'total': 6}, default=json_serial)}\n\n"
                        
                    except Exception as e:
                        logger.error(f"Error generating {difficulty} assignment {i+1}: {str(e)}")
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to generate {difficulty} assignment {i+1}: {str(e)}'})}\n\n"
            
            # Commit all assignments
            db.commit()
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete', 'message': 'All assignments generated successfully!', 'total': 6, 'completed': completed})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in progressive generation: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Generation failed: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.put("/assignments/{assignment_id}")
async def edit_assignment(
    assignment_id: str,
    request: AssignmentEditRequest,
    db: Session = Depends(get_db)
):
    """Edit an assignment and update its tags"""
    try:
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Update assignment
        assignment.title = request.title
        assignment.description = request.description
        assignment.reason_for_change = request.reason_for_change
        assignment.version += 1
        
        # Update tags - replace AI-Generated with Modified
        old_tags = assignment.tags.copy() if assignment.tags else []
        new_tags = assignment.tags.copy() if assignment.tags else []
        if "AI-Generated" in new_tags:
            new_tags.remove("AI-Generated")
        if "Modified" not in new_tags:
            new_tags.append("Modified")
        assignment.tags = new_tags
        
        logger.info(f"Updated assignment {assignment_id} tags:")
        logger.info(f"  Old tags: {old_tags}")
        logger.info(f"  New tags: {new_tags}")
        
        db.commit()
        
        return {
            "message": "Assignment updated successfully",
            "assignment_id": assignment_id,
            "version": assignment.version,
            "tags": assignment.tags
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error editing assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to edit assignment: {str(e)}")

@router.post("/rubric/generate")
async def generate_rubric(
    request: RubricGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate rubric for selected assignments"""
    try:
        if not request.assignment_ids:
            raise HTTPException(status_code=400, detail="At least one assignment must be selected")
        
        # Get selected assignments
        assignments = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id.in_([uuid.UUID(aid) for aid in request.assignment_ids])
        ).all()
        
        if not assignments:
            raise HTTPException(status_code=404, detail="No assignments found")
        
        # Combine assignment descriptions for rubric generation
        combined_text = "\n\n".join([
            f"Assignment {i+1}: {assignment.title}\n{assignment.description}"
            for i, assignment in enumerate(assignments)
        ])
        
        # Initialize rubric service
        rubric_service = RubricService()
        
        # Generate rubric
        rubric_data = await rubric_service.generate_rubric(
            text=combined_text,
            doc_type="Situated Learning Assignment"
        )
        
        # Save to database with custom name if provided
        rubric_name = request.rubric_name or rubric_data.get("rubric_name", "Generated Rubric")
        
        # Update the rubric_data to use the user-provided name consistently
        rubric_data["rubric_name"] = rubric_name
        
        db_rubric = DBAssignmentRubric(
            id=uuid.uuid4(),
            assignment_ids=[assignment.id for assignment in assignments],
            rubric_name=rubric_name,
            doc_type=rubric_data.get("doc_type", "Assignment"),
            criteria=rubric_data
        )
        
        db.add(db_rubric)
        db.commit()
        
        return {
            "message": "Rubric generated successfully",
            "rubric_id": str(db_rubric.id),
            "rubric": rubric_data
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating rubric: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate rubric: {str(e)}")

@router.put("/rubric/{rubric_id}")
async def edit_rubric(
    rubric_id: str,
    request: RubricEditRequest,
    db: Session = Depends(get_db)
):
    """Edit a rubric and mark it as edited"""
    try:
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.id == uuid.UUID(rubric_id)
        ).first()
        
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        # Update rubric - update both individual columns and criteria
        old_rubric_name = rubric.rubric_name
        old_doc_type = rubric.doc_type
        
        rubric.rubric_name = request.criteria.get('rubric_name', rubric.rubric_name)
        rubric.doc_type = request.criteria.get('doc_type', rubric.doc_type)
        rubric.criteria = request.criteria
        
        # Only mark as edited if it's not just a name/type change
        if not request.name_only_change:
            rubric.is_edited = True
        rubric.reason_for_edit = request.reason_for_edit
        
        logger.info(f"Updated rubric {rubric_id}:")
        logger.info(f"  Rubric name: {old_rubric_name} -> {rubric.rubric_name}")
        logger.info(f"  Doc type: {old_doc_type} -> {rubric.doc_type}")
        logger.info(f"  Is edited: {rubric.is_edited}")
        
        db.commit()
        
        return {
            "message": "Rubric updated successfully",
            "rubric_id": rubric_id,
            "is_edited": rubric.is_edited
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rubric ID format")
    except Exception as e:
        db.rollback()
        logger.error(f"Error editing rubric {rubric_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to edit rubric: {str(e)}")

@router.get("/rubric/{rubric_id}/download")
async def download_rubric(
    rubric_id: str,
    db: Session = Depends(get_db)
):
    """Download a rubric as a Word document"""
    try:
        rubric = db.query(DBAssignmentRubric).filter(
            DBAssignmentRubric.id == uuid.UUID(rubric_id)
        ).first()
        
        if not rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        
        # Generate Word document
        from services.document_service import generate_rubric_download
        
        doc_bytes = generate_rubric_download(rubric.criteria)
        
        return StreamingResponse(
            io.BytesIO(doc_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={rubric.rubric_name or 'Rubric'}_Rubric.docx"}
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rubric ID format")
    except Exception as e:
        logger.error(f"Error downloading rubric {rubric_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download rubric: {str(e)}")

@router.post("/assignments/save")
async def save_assignment(
    request: SaveAssignmentRequest,
    db: Session = Depends(get_db)
):
    """Save selected assignments with a user-provided name"""
    try:
        if not request.selected_assignment_ids:
            raise HTTPException(status_code=400, detail="At least one assignment must be selected")
        
        # Update selected assignments
        assignments = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id.in_([uuid.UUID(aid) for aid in request.selected_assignment_ids])
        ).all()
        
        if not assignments:
            raise HTTPException(status_code=404, detail="No assignments found")
        
        # Update assignments with the provided name and mark as selected
        for assignment in assignments:
            assignment.assignment_name = request.assignment_name
            assignment.is_selected = True
        
        db.commit()
        
        return {
            "message": f"Assignment '{request.assignment_name}' saved successfully",
            "assignment_count": len(assignments),
            "rubric_id": request.rubric_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save assignment: {str(e)}")

@router.get("/assignments/{assignment_id}/download")
async def download_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Download single assignment as Word document"""
    try:
        from services.document_service import DocumentService
        document_service = DocumentService()
        
        return document_service.generate_single_assignment_download(db, assignment_id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading assignment {assignment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download: {str(e)}")

@router.post("/assignments/download")
async def download_multiple_assignments(
    assignment_ids: List[str],
    assignment_name: str = "Generated Assignments",
    db: Session = Depends(get_db)
):
    """Download multiple assignments as Word document"""
    try:
        if not assignment_ids:
            raise HTTPException(status_code=400, detail="At least one assignment ID must be provided")
        
        from services.document_service import DocumentService
        document_service = DocumentService()
        
        return document_service.generate_multiple_assignments_download(
            db, assignment_ids, assignment_name
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download: {str(e)}")

# Helper functions

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

def extract_title_from_content(content: str) -> str:
    """Extract title from assignment content"""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Take first meaningful line as title, truncate if too long
            title = line.replace('**', '').replace('*', '').strip()
            return title[:200] if len(title) > 200 else title
    
    return "Generated Assignment"
