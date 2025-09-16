"""
Comprehensive PDF Report Generator for Evaluation Results
Creates professional, detailed evaluation reports with all submission details
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)

class EvaluationReportGenerator:
    """Generate comprehensive PDF reports for evaluation results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Heading styles
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkgreen
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Feedback style
        self.styles.add(ParagraphStyle(
            name='Feedback',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leftIndent=10,
            rightIndent=10,
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=5
        ))
        
        # Score style
        self.styles.add(ParagraphStyle(
            name='Score',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=4,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontWeight='bold'
        ))

    def generate_evaluation_report(self, assignment_data: Dict[str, Any], 
                                 evaluation_results: List[Dict[str, Any]], 
                                 rubric_data: Dict[str, Any]) -> bytes:
        """
        Generate comprehensive evaluation report PDF
        
        Args:
            assignment_data: Assignment information
            evaluation_results: List of evaluation results for all submissions
            rubric_data: Rubric information and criteria
            
        Returns:
            PDF content as bytes
        """
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Build the story (content)
            story = []
            
            # Add title page
            story.extend(self._create_title_page(assignment_data))
            story.append(PageBreak())
            
            # Add executive summary
            story.extend(self._create_executive_summary(evaluation_results))
            story.append(PageBreak())
            
            # Add rubric details
            story.extend(self._create_rubric_section(rubric_data))
            story.append(PageBreak())
            
            # Add individual submission results
            for i, result in enumerate(evaluation_results, 1):
                story.extend(self._create_submission_section(result, i))
                if i < len(evaluation_results):  # Don't add page break after last submission
                    story.append(PageBreak())
            
            # Add page break before summary statistics
            story.append(PageBreak())
            
            # Add summary statistics
            story.extend(self._create_summary_statistics(evaluation_results))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"Successfully generated evaluation report with {len(evaluation_results)} submissions")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating evaluation report: {str(e)}")
            raise Exception(f"Report generation failed: {str(e)}")

    def _create_title_page(self, assignment_data: Dict[str, Any]) -> List:
        """Create the title page of the report"""
        elements = []
        
        # Main title
        elements.append(Paragraph("Situated Learning Evaluation Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        
        # Assignment details
        elements.append(Paragraph("Assignment Details", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 10))
        
        assignment_info = [
            ["Assignment Name:", assignment_data.get('assignment_name', 'N/A')],
            ["Title:", assignment_data.get('title', 'N/A')],
            ["Course:", assignment_data.get('course_title', 'N/A')],
            ["Academic Year:", assignment_data.get('academic_year', 'N/A')],
            ["Semester:", assignment_data.get('semester', 'N/A')],
            ["Generated On:", datetime.now().strftime("%B %d, %Y at %I:%M %p")]
        ]
        
        assignment_table = Table(assignment_info, colWidths=[2*inch, 4*inch])
        assignment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(assignment_table)
        elements.append(Spacer(1, 20))
        
        # Assignment description
        if assignment_data.get('description'):
            elements.append(Paragraph("Assignment Description", self.styles['CustomHeading2']))
            elements.append(Paragraph(assignment_data['description'], self.styles['CustomBody']))
        
        return elements

    def _create_executive_summary(self, evaluation_results: List[Dict[str, Any]]) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 10))
        
        # Calculate summary statistics
        total_submissions = len(evaluation_results)
        scores = [result.get('overall_score', 0) for result in evaluation_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        # Performance distribution
        excellent = len([s for s in scores if s >= 16])  # 80%+
        good = len([s for s in scores if 12 <= s < 16])  # 60-79%
        satisfactory = len([s for s in scores if 8 <= s < 12])  # 40-59%
        needs_improvement = len([s for s in scores if s < 8])  # <40%
        
        summary_data = [
            ["Total Submissions:", str(total_submissions)],
            ["Average Score:", f"{avg_score:.1f}/20 ({(avg_score/20)*100:.1f}%)"],
            ["Highest Score:", f"{max_score:.1f}/20 ({(max_score/20)*100:.1f}%)"],
            ["Lowest Score:", f"{min_score:.1f}/20 ({(min_score/20)*100:.1f}%)"],
            ["", ""],
            ["Performance Distribution:", ""],
            ["Excellent (80%+):", f"{excellent} submissions"],
            ["Good (60-79%):", f"{good} submissions"],
            ["Satisfactory (40-59%):", f"{satisfactory} submissions"],
            ["Needs Improvement (<40%):", f"{needs_improvement} submissions"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 15))
        
        # Key insights
        elements.append(Paragraph("Key Insights", self.styles['CustomHeading2']))
        
        insights = []
        if excellent > 0:
            insights.append(f"• {excellent} submission(s) achieved excellent performance (80%+)")
        if needs_improvement > 0:
            insights.append(f"• {needs_improvement} submission(s) require significant improvement")
        if avg_score >= 12:
            insights.append("• Overall class performance is above average")
        elif avg_score < 8:
            insights.append("• Overall class performance indicates need for additional support")
        
        for insight in insights:
            elements.append(Paragraph(insight, self.styles['CustomBody']))
        
        return elements

    def _create_rubric_section(self, rubric_data: Dict[str, Any]) -> List:
        """Create rubric details section"""
        elements = []
        
        elements.append(Paragraph("Evaluation Rubric", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 10))
        
        # Rubric information
        elements.append(Paragraph(f"<b>Rubric Name:</b> {rubric_data.get('rubric_name', 'N/A')}", self.styles['CustomBody']))
        elements.append(Paragraph(f"<b>Document Type:</b> {rubric_data.get('doc_type', 'N/A')}", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Rubric criteria
        criteria = rubric_data.get('rubrics', [])
        for i, criterion in enumerate(criteria, 1):
            elements.append(Paragraph(f"{i}. {criterion.get('category', 'Unknown Category')}", self.styles['CustomHeading2']))
            
            questions = criterion.get('questions', [])
            for j, question in enumerate(questions, 1):
                elements.append(Paragraph(f"   {j}. {question}", self.styles['CustomBody']))
            
            elements.append(Spacer(1, 8))
        
        return elements

    def _create_submission_section(self, result: Dict[str, Any], submission_number: int) -> List:
        """Create detailed section for individual submission"""
        elements = []
        
        # Submission header
        elements.append(Paragraph(f"Submission {submission_number}", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 10))
        
        # Basic information
        elements.append(Paragraph("Submission Details", self.styles['CustomHeading2']))
        
        submission_info = [
            ["File Name:", result.get('file_name', 'N/A')],
            ["Overall Score:", f"{result.get('overall_score', 0):.1f}/20 ({(result.get('overall_score', 0)/20)*100:.1f}%)"],
            ["Faculty Reviewed:", "Yes" if result.get('faculty_reviewed', False) else "No"]
        ]
        
        if result.get('faculty_feedback'):
            submission_info.append(["Faculty Feedback:", "See detailed feedback below"])
        
        info_table = Table(submission_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        # Overall feedback
        if result.get('overall_feedback'):
            elements.append(Paragraph("Overall Feedback", self.styles['CustomHeading2']))
            elements.append(Paragraph(result['overall_feedback'], self.styles['Feedback']))
            elements.append(Spacer(1, 10))
        
        # Criterion-wise results
        criterion_results = result.get('criterion_results', [])
        if criterion_results:
            elements.append(Paragraph("Criterion-wise Performance", self.styles['CustomHeading2']))
            
            for criterion in criterion_results:
                elements.append(Paragraph(f"<b>{criterion.get('category', 'Unknown')}</b>", self.styles['CustomBody']))
                
                # Criterion score
                score_text = f"Score: {criterion.get('score', 0):.1f}/{criterion.get('max_score', 0)} ({criterion.get('percentage', 0):.0f}%)"
                elements.append(Paragraph(score_text, self.styles['Score']))
                
                # Add spacing between score and feedback
                elements.append(Spacer(1, 6))
                
                # Criterion feedback
                if criterion.get('feedback'):
                    elements.append(Paragraph(criterion['feedback'], self.styles['Feedback']))
                
                elements.append(Spacer(1, 8))
        
        # Faculty adjustments (if any)
        if result.get('faculty_adjustments'):
            elements.append(Paragraph("Faculty Adjustments", self.styles['CustomHeading2']))
            elements.append(Paragraph("This submission was reviewed and adjusted by faculty.", self.styles['CustomBody']))
            
            if result.get('faculty_feedback'):
                elements.append(Paragraph("Faculty Comments:", self.styles['CustomBody']))
                elements.append(Paragraph(result['faculty_feedback'], self.styles['Feedback']))
        
        return elements

    def _create_summary_statistics(self, evaluation_results: List[Dict[str, Any]]) -> List:
        """Create summary statistics section"""
        elements = []
        
        elements.append(Paragraph("Summary Statistics", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 10))
        
        # Calculate detailed statistics
        scores = [result.get('overall_score', 0) for result in evaluation_results]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            sorted_scores = sorted(scores)
            median_score = sorted_scores[len(sorted_scores)//2] if len(sorted_scores) % 2 == 1 else (sorted_scores[len(sorted_scores)//2-1] + sorted_scores[len(sorted_scores)//2]) / 2
            
            # Standard deviation
            variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
            std_dev = variance ** 0.5
            
            stats_data = [
                ["Statistic", "Value"],
                ["Total Submissions", str(len(scores))],
                ["Average Score", f"{avg_score:.2f}/20 ({(avg_score/20)*100:.1f}%)"],
                ["Median Score", f"{median_score:.2f}/20 ({(median_score/20)*100:.1f}%)"],
                ["Standard Deviation", f"{std_dev:.2f}"],
                ["Highest Score", f"{max(scores):.2f}/20 ({(max(scores)/20)*100:.1f}%)"],
                ["Lowest Score", f"{min(scores):.2f}/20 ({(min(scores)/20)*100:.1f}%)"]
            ]
            
            stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
            stats_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(stats_table)
        
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey))
        elements.append(Spacer(1, 10))
        
        # Footer
        elements.append(Paragraph("Generated by Situated Learning Evaluation System", self.styles['CustomBody']))
        elements.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomBody']))
        
        return elements
