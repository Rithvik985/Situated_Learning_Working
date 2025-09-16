"""
Analytics router for comprehensive system analytics and reporting
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from database.repository import get_db
from database.models import (
    Course, PastAssignment, GeneratedAssignment, AssignmentRubric,
    StudentSubmission, EvaluationResult
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Response Models
class OverviewMetrics(BaseModel):
    total_courses: int
    total_past_assignments: int
    total_generated_assignments: int
    total_student_submissions: int
    total_evaluations: int
    assignment_modification_rate: float
    rubric_edit_rate: float

class UsageAnalytics(BaseModel):
    daily_usage: List[Dict[str, Any]]
    course_activity: List[Dict[str, Any]]
    popular_topics: List[Dict[str, Any]]
    popular_domains: List[Dict[str, Any]]

class ContentAnalytics(BaseModel):
    assignment_modifications: List[Dict[str, Any]]
    rubric_edits: List[Dict[str, Any]]
    difficulty_distribution: List[Dict[str, Any]]
    version_analytics: List[Dict[str, Any]]

class LearningAnalytics(BaseModel):
    score_distributions: List[Dict[str, Any]]
    evaluation_trends: List[Dict[str, Any]]
    faculty_adjustments: List[Dict[str, Any]]

@router.get("/overview", response_model=OverviewMetrics)
async def get_overview_metrics(
    course_filter: Optional[str] = Query(None, description="Filter by course title"),
    academic_year_filter: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """Get overview metrics for the dashboard"""
    try:
        # Base queries with optional filters
        course_query = db.query(Course)
        if course_filter:
            course_query = course_query.filter(Course.title.ilike(f"%{course_filter}%"))
        if academic_year_filter:
            course_query = course_query.filter(Course.academic_year == academic_year_filter)
        
        # Get filtered course IDs
        course_ids = [c.id for c in course_query.all()]
        
        # Total counts
        total_courses = len(course_ids)
        
        past_assignments_query = db.query(PastAssignment)
        if course_ids:
            past_assignments_query = past_assignments_query.filter(PastAssignment.course_id.in_(course_ids))
        total_past_assignments = past_assignments_query.count()
        
        generated_assignments_query = db.query(GeneratedAssignment)
        if course_ids:
            generated_assignments_query = generated_assignments_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        total_generated_assignments = generated_assignments_query.count()
        
        # Assignment modification rate (AI-Generated vs Modified tags)
        modified_assignments = generated_assignments_query.filter(
            ~GeneratedAssignment.tags.op('@>')(['AI-Generated'])
        ).count()
        
        assignment_modification_rate = (
            (modified_assignments / total_generated_assignments * 100) 
            if total_generated_assignments > 0 else 0
        )
        
        # Rubric edit rate
        rubrics_query = db.query(AssignmentRubric)
        if course_ids:
            # Filter rubrics that have assignments in the specified courses
            # Get assignment IDs for the filtered courses
            assignment_ids_in_courses = db.query(GeneratedAssignment.id).filter(
                GeneratedAssignment.course_id.in_(course_ids)
            ).all()
            assignment_ids = [aid[0] for aid in assignment_ids_in_courses]
            
            if assignment_ids:
                # Use UNNEST to check array overlap
                rubrics_query = rubrics_query.filter(
                    AssignmentRubric.assignment_ids.overlap(assignment_ids)
                )
        total_rubrics = rubrics_query.count()
        edited_rubrics = rubrics_query.filter(AssignmentRubric.is_edited == True).count()
        
        rubric_edit_rate = (
            (edited_rubrics / total_rubrics * 100) 
            if total_rubrics > 0 else 0
        )
        
        # Student submissions and evaluations
        submissions_query = db.query(StudentSubmission).join(
            GeneratedAssignment,
            StudentSubmission.assignment_id == GeneratedAssignment.id
        )
        if course_ids:
            submissions_query = submissions_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        total_student_submissions = submissions_query.count()
        
        evaluations_query = db.query(EvaluationResult).join(
            GeneratedAssignment,
            EvaluationResult.assignment_id == GeneratedAssignment.id
        )
        if course_ids:
            evaluations_query = evaluations_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        total_evaluations = evaluations_query.count()
        
        return OverviewMetrics(
            total_courses=total_courses,
            total_past_assignments=total_past_assignments,
            total_generated_assignments=total_generated_assignments,
            total_student_submissions=total_student_submissions,
            total_evaluations=total_evaluations,
            assignment_modification_rate=round(assignment_modification_rate, 2),
            rubric_edit_rate=round(rubric_edit_rate, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting overview metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview metrics: {str(e)}")

@router.get("/usage", response_model=UsageAnalytics)
async def get_usage_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    course_filter: Optional[str] = Query(None, description="Filter by course title"),
    academic_year_filter: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """Get usage analytics and trends"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Base course filter
        course_query = db.query(Course)
        if course_filter:
            course_query = course_query.filter(Course.title.ilike(f"%{course_filter}%"))
        if academic_year_filter:
            course_query = course_query.filter(Course.academic_year == academic_year_filter)
        course_ids = [c.id for c in course_query.all()]
        
        # Daily usage trends
        daily_generated = db.query(
            func.date(GeneratedAssignment.created_at).label('date'),
            func.count(GeneratedAssignment.id).label('generated_count')
        ).filter(
            GeneratedAssignment.created_at >= start_date,
            GeneratedAssignment.created_at <= end_date
        )
        
        if course_ids:
            daily_generated = daily_generated.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        daily_generated = daily_generated.group_by(func.date(GeneratedAssignment.created_at)).all()
        
        # Combine daily usage data
        daily_usage = []
        for i in range(days):
            current_date = (start_date + timedelta(days=i)).date()
            generated_count = next((d.generated_count for d in daily_generated if d.date == current_date), 0)
            
            daily_usage.append({
                "date": current_date.isoformat(),
                "generated_assignments": generated_count
            })
        
        # Course activity
        course_activity_query = db.query(
            Course.title,
            Course.course_code,
            Course.academic_year,
            func.count(GeneratedAssignment.id).label('assignment_count')
        ).outerjoin(
            GeneratedAssignment,
            Course.id == GeneratedAssignment.course_id
        )
        
        if course_ids:
            course_activity_query = course_activity_query.filter(Course.id.in_(course_ids))
        
        course_activity = course_activity_query.group_by(
            Course.id, Course.title, Course.course_code, Course.academic_year
        ).order_by(desc(func.count(GeneratedAssignment.id))).limit(10).all()
        
        course_activity_list = [
            {
                "course_title": ca.title,
                "course_code": ca.course_code,
                "academic_year": ca.academic_year,
                "assignment_count": ca.assignment_count
            }
            for ca in course_activity
        ]
        
        # Popular topics and domains - simplified for now
        popular_topics = [{"topic": "Sample Topic", "count": 5}]
        popular_domains = [{"domain": "Sample Domain", "count": 3}]
        
        return UsageAnalytics(
            daily_usage=daily_usage,
            course_activity=course_activity_list,
            popular_topics=popular_topics,
            popular_domains=popular_domains
        )
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage analytics: {str(e)}")

@router.get("/content", response_model=ContentAnalytics)
async def get_content_analytics(
    course_filter: Optional[str] = Query(None, description="Filter by course title"),
    academic_year_filter: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """Get content analytics including modifications and edits"""
    try:
        # Base course filter
        course_query = db.query(Course)
        if course_filter:
            course_query = course_query.filter(Course.title.ilike(f"%{course_filter}%"))
        if academic_year_filter:
            course_query = course_query.filter(Course.academic_year == academic_year_filter)
        course_ids = [c.id for c in course_query.all()]
        
        # Assignment modifications analysis
        modifications_query = db.query(
            GeneratedAssignment.course_name,
            func.count(GeneratedAssignment.id).label('total_assignments'),
            func.sum(case(
                (GeneratedAssignment.tags.op('@>')(['AI-Generated']), 0),
                else_=1
            )).label('modified_assignments')
        )
        
        if course_ids:
            modifications_query = modifications_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        modifications = modifications_query.group_by(GeneratedAssignment.course_name).all()
        
        assignment_modifications = []
        for mod in modifications:
            total = mod.total_assignments or 0
            modified = mod.modified_assignments or 0
            modification_rate = (modified / total * 100) if total > 0 else 0
            
            assignment_modifications.append({
                "course_name": mod.course_name,
                "total_assignments": total,
                "modified_assignments": modified,
                "modification_rate": round(modification_rate, 2)
            })
        
        # Rubric edits analysis
        rubric_edits_query = db.query(
            func.count(AssignmentRubric.id).label('total_rubrics'),
            func.sum(case(
                (AssignmentRubric.is_edited == True, 1),
                else_=0
            )).label('edited_rubrics')
        )
        
        if course_ids:
            # Filter rubrics that have assignments in the specified courses
            # Get assignment IDs for the filtered courses
            assignment_ids_in_courses = db.query(GeneratedAssignment.id).filter(
                GeneratedAssignment.course_id.in_(course_ids)
            ).all()
            assignment_ids = [aid[0] for aid in assignment_ids_in_courses]
            
            if assignment_ids:
                # Use UNNEST to check array overlap
                rubric_edits_query = rubric_edits_query.filter(
                    AssignmentRubric.assignment_ids.overlap(assignment_ids)
                )
        
        rubric_edits = rubric_edits_query.first()
        
        total_rubrics = rubric_edits.total_rubrics or 0
        edited_rubrics = rubric_edits.edited_rubrics or 0
        edit_rate = (edited_rubrics / total_rubrics * 100) if total_rubrics > 0 else 0
        
        rubric_edits_list = [{
            "total_rubrics": total_rubrics,
            "edited_rubrics": edited_rubrics,
            "edit_rate": round(edit_rate, 2)
        }]
        
        # Difficulty distribution
        difficulty_query = db.query(
            GeneratedAssignment.difficulty_level,
            func.count(GeneratedAssignment.id).label('count')
        )
        
        if course_ids:
            difficulty_query = difficulty_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        difficulty_dist = difficulty_query.group_by(GeneratedAssignment.difficulty_level).all()
        
        difficulty_distribution = [
            {
                "difficulty": diff.difficulty_level,
                "count": diff.count
            }
            for diff in difficulty_dist
        ]
        
        # Version analytics
        version_query = db.query(
            GeneratedAssignment.version,
            func.count(GeneratedAssignment.id).label('count')
        )
        
        if course_ids:
            version_query = version_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        versions = version_query.group_by(GeneratedAssignment.version).all()
        
        version_analytics = [
            {
                "version": ver.version,
                "count": ver.count
            }
            for ver in versions
        ]
        
        return ContentAnalytics(
            assignment_modifications=assignment_modifications,
            rubric_edits=rubric_edits_list,
            difficulty_distribution=difficulty_distribution,
            version_analytics=version_analytics
        )
        
    except Exception as e:
        logger.error(f"Error getting content analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get content analytics: {str(e)}")

@router.get("/learning", response_model=LearningAnalytics)
async def get_learning_analytics(
    course_filter: Optional[str] = Query(None, description="Filter by course title"),
    academic_year_filter: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """Get learning analytics and student performance metrics"""
    try:
        # Base course filter
        course_query = db.query(Course)
        if course_filter:
            course_query = course_query.filter(Course.title.ilike(f"%{course_filter}%"))
        if academic_year_filter:
            course_query = course_query.filter(Course.academic_year == academic_year_filter)
        course_ids = [c.id for c in course_query.all()]
        
        # Score distributions
        score_query = db.query(
            case(
                (EvaluationResult.overall_score >= 18, 'Excellent (18-20)'),
                (EvaluationResult.overall_score >= 15, 'Good (15-17)'),
                (EvaluationResult.overall_score >= 12, 'Average (12-14)'),
                (EvaluationResult.overall_score >= 10, 'Below Average (10-11)'),
                else_='Poor (<10)'
            ).label('score_range'),
            func.count(EvaluationResult.id).label('count')
        ).join(
            GeneratedAssignment,
            EvaluationResult.assignment_id == GeneratedAssignment.id
        )
        
        if course_ids:
            score_query = score_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        score_dist = score_query.group_by('score_range').all()
        
        score_distributions = [
            {
                "score_range": score.score_range,
                "count": score.count
            }
            for score in score_dist
        ]
        
        # Faculty adjustments
        adjustments_query = db.query(
            func.count(EvaluationResult.id).label('total_evaluations'),
            func.sum(case(
                (EvaluationResult.faculty_reviewed == True, 1),
                else_=0
            )).label('faculty_reviewed'),
            func.avg(EvaluationResult.faculty_score_adjustment).label('avg_adjustment')
        ).join(
            GeneratedAssignment,
            EvaluationResult.assignment_id == GeneratedAssignment.id
        )
        
        if course_ids:
            adjustments_query = adjustments_query.filter(GeneratedAssignment.course_id.in_(course_ids))
        
        adjustments = adjustments_query.first()
        
        faculty_adjustments = [{
            "total_evaluations": adjustments.total_evaluations or 0,
            "faculty_reviewed": adjustments.faculty_reviewed or 0,
            "average_adjustment": round(float(adjustments.avg_adjustment), 2) if adjustments.avg_adjustment else 0,
            "review_rate": round((adjustments.faculty_reviewed / adjustments.total_evaluations * 100), 2) if adjustments.total_evaluations else 0
        }]
        
        return LearningAnalytics(
            score_distributions=score_distributions,
            evaluation_trends=[],
            faculty_adjustments=faculty_adjustments
        )
        
    except Exception as e:
        logger.error(f"Error getting learning analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning analytics: {str(e)}")

@router.get("/courses")
async def get_courses_for_filter(db: Session = Depends(get_db)):
    """Get list of courses for filtering"""
    try:
        courses = db.query(Course.title, Course.academic_year).distinct().all()
        
        course_titles = list(set([c.title for c in courses]))
        academic_years = list(set([c.academic_year for c in courses]))
        
        return {
                    "course_titles": sorted(course_titles),
                    "academic_years": sorted(academic_years, reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Error getting courses for filter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get courses: {str(e)}")

@router.get("/export")
async def export_analytics_report(
    course_filter: Optional[str] = Query(None, description="Filter by course title"),
    academic_year_filter: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """Export analytics data as PDF report"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
        
        # Get high-level analytics data only
        overview_data = await get_overview_metrics(course_filter, academic_year_filter, db)
        usage_data = await get_usage_analytics(30, course_filter, academic_year_filter, db)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Situated Learning Analytics Report", title_style))
        story.append(Spacer(1, 12))
        
        # Report info
        report_date = datetime.now().strftime("%B %d, %Y")
        filters_text = ""
        if course_filter:
            filters_text += f"<br/>Course Filter: {course_filter}"
        if academic_year_filter:
            filters_text += f"<br/>Academic Year: {academic_year_filter}"
        
        story.append(Paragraph(f"<b>Report Date:</b> {report_date}{filters_text}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Overview Metrics
        story.append(Paragraph("System Overview", heading_style))
        
        overview_table_data = [
            ['Metric', 'Value'],
            ['Total Courses', str(overview_data.total_courses)],
            ['Past Assignments', str(overview_data.total_past_assignments)],
            ['Generated Assignments', str(overview_data.total_generated_assignments)],
            ['Student Submissions', str(overview_data.total_student_submissions)],
            ['Evaluations Completed', str(overview_data.total_evaluations)],
            ['Assignment Modification Rate', f"{overview_data.assignment_modification_rate}%"],
            ['Rubric Edit Rate', f"{overview_data.rubric_edit_rate}%"]
        ]
        
        overview_table = Table(overview_table_data, colWidths=[3*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Usage Summary
        story.append(Paragraph("Usage Summary", heading_style))
        
        # Get top 5 most active courses
        top_courses = usage_data.course_activity[:5] if usage_data.course_activity else []
        
        if top_courses:
            usage_table_data = [['Course', 'Assignments Generated']]
            for course in top_courses:
                usage_table_data.append([course['course_title'], str(course['assignment_count'])])
            
            usage_table = Table(usage_table_data, colWidths=[4*inch, 1.5*inch])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(usage_table)
        else:
            story.append(Paragraph("No usage data available for the selected filters.", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph("Summary", heading_style))
        summary_text = f"""
        This report provides a high-level overview of the Situated Learning system analytics.
        The system currently manages {overview_data.total_courses} courses with {overview_data.total_generated_assignments} 
        generated assignments and {overview_data.total_evaluations} completed evaluations.
        
        Key insights:
        • {overview_data.assignment_modification_rate}% of generated assignments have been modified from their AI-generated state
        • {overview_data.rubric_edit_rate}% of rubrics have been edited by faculty
        • The system has processed {overview_data.total_student_submissions} student submissions
        
        For detailed analytics and interactive charts, please use the web interface.
        """
        
        story.append(Paragraph(summary_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Return PDF
        from fastapi.responses import Response
        
        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
