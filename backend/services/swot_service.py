import json
import httpx
import logging
from uuid import uuid4
from typing import Dict, Any
from config.settings import settings
from utils.llm_config import llm_config
from sqlalchemy.orm import Session
import re
from database.models import (
    GeneratedAssignment as DBGeneratedAssignment,
    StudentSWOTResult as DBStudentSWOT,
    SWOTSubmission,
)
from schemas.schemas import SubmissionCreate  # for validation


logger = logging.getLogger(__name__)

class LLMAnalysisService:
    def __init__(self):
        self.timeout = 480
        self.base_url = llm_config.text_model_url
        self.model_name = llm_config.text_model_name
        self.headers = llm_config.get_headers()

    async def analyze_submission(self, request, db: Session, submission_id: str) -> Dict[str, Any]:
        """Perform SWOT analysis using LLM and store submission + SWOT results in DB."""
        # Fetch assignment
        assignment = db.query(DBGeneratedAssignment).filter(
            DBGeneratedAssignment.id == request.assignment_id
        ).first()

        if not assignment:
            raise Exception("Assignment not found")

        # Create prompts
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(assignment, request.content)

        try:
            # Call LLM
            response_text = await self._call_llm(system_prompt, user_prompt)
            swot_analysis = self._parse_swot_response(response_text)

            # ✅ Create submission entry
            submission_data = SubmissionCreate(
                student_id=request.student_id,
                assignment_id=request.assignment_id,
                content=request.content,
                evaulation_status="draft",
            )
            submission = self._create_submission(db, submission_data)

            # ✅ Store SWOT analysis
            swot_result = DBStudentSWOT(
                id=str(uuid4()),
                submission_id=str(submission.id),
                strengths=swot_analysis.get("strengths", []),
                weaknesses=swot_analysis.get("weaknesses", []),
                opportunities=swot_analysis.get("opportunities", []),
                threats=swot_analysis.get("threats", []),
                suggestions=swot_analysis.get("suggestions", []),
            )

            db.add(swot_result)
            db.commit()
            db.refresh(swot_result)

            return {
                "strengths": swot_analysis.get("strengths", []),
                "weaknesses": swot_analysis.get("weaknesses", []),
                "opportunities": swot_analysis.get("opportunities", []),
                "threats": swot_analysis.get("threats", []),
                "suggestions": swot_analysis.get("suggestions", []),
                "submission_id": str(submission.id)  # This goes INSIDE the main object
            }


        except Exception as e:
            logger.error(f"Error generating SWOT analysis: {str(e)}")
            db.rollback()
            raise

    def _create_submission(self, db: Session, submission_data: SubmissionCreate):
        """Create a new SWOT submission entry."""
        new_submission = SWOTSubmission(
            id=str(uuid4()),
            student_id=submission_data.student_id,
            content=submission_data.content,
            processing_status="completed",
            evaluation_status=submission_data.evaluation_status,
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)
        return new_submission

    def _create_system_prompt(self) -> str:
        return """You are an expert academic evaluator performing SWOT analysis on student submissions.
Your goal is to provide structured, specific, and actionable insights that help the student improve
their work while aligning with assignment objectives."""

    def _create_user_prompt(self, assignment, student_content: str) -> str:
        return f"""
You are evaluating a student's submission for the following assignment:

Assignment Title: {assignment.title}
Assignment Description: {assignment.description}
Course: {assignment.course_name}

Analyze the student's submission using the SWOT framework.
Provide at the maximum three concise bullet points for each SWOT category.
If there are no points to mention in a category, respond with 'N/A' for that category.
### Student Submission:
{student_content}

Respond in the following structure:
Strengths:
- ...
Weaknesses:
- ...
Opportunities:
- ...
Threats:
- ...
Suggestions:
- ...
"""

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Asynchronous call to the LLM endpoint."""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1500
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.base_url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            except httpx.RequestError as e:
                logger.error(f"LLM SWOT API request failed: {str(e)}")
                raise Exception(f"SWOT LLM request failed: {str(e)}")
            except KeyError:
                raise Exception("Unexpected response format from LLM")

    # def _parse_swot_response(self, response_text: str) -> Dict[str, list]:
    #     logger.info(f"🔍 Raw LLM SWOT response:\n{response_text}")
    #     swot_sections = {}
    #     current_section = None

    #     for line in response_text.split("\n"):
    #         line = line.strip()
    #         if not line:
    #             continue

    #         lower = line.lower()
    #         if "strengths:" in lower:
    #             current_section = "strengths"
    #             swot_sections[current_section] = []
    #         elif "weaknesses:" in lower:
    #             current_section = "weaknesses"
    #             swot_sections[current_section] = []
    #         elif "opportunities:" in lower:
    #             current_section = "opportunities"
    #             swot_sections[current_section] = []
    #         elif "threats:" in lower:
    #             current_section = "threats"
    #             swot_sections[current_section] = []
    #         elif "suggestions:" in lower:
    #             current_section = "suggestions"
    #             swot_sections[current_section] = []
    #         elif current_section:
    #             # Remove bullet point markers and stars
    #             cleaned_line = line.lstrip("- *")  # Remove leading bullet points and spaces
    #             cleaned_line = cleaned_line.replace("**", "")  # Remove double stars
    #             cleaned_line = cleaned_line.strip()  # Clean up any remaining whitespace
    #             if cleaned_line:  # Only add non-empty lines
    #                 swot_sections[current_section].append(cleaned_line)

    # #     return swot_sections
    def _parse_swot_response(self, response_text: str) -> Dict[str, list]:
        import re, json
        logger.info(f"🔍 Raw LLM SWOT response:\n{response_text}")

        # Initialize keys with empty lists so response always has the keys
        sections = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "suggestions": [],
        }

        # Regex to match header lines (e.g. "#### Strengths:", "**Strengths**:", "Strengths:")
        header_regex = re.compile(
            r"^(?:\s*(?:#+\s*)?|\s*\*\*?)(strengths?|weaknesses?|opportunities?|threats?|suggestions?)\b[:\-]?",
            re.IGNORECASE,
        )

        current = None
        for raw_line in response_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # If the line is a header => switch section
            m = header_regex.match(line)
            if m:
                key_word = m.group(1).lower()
                if key_word.startswith("strength"):
                    current = "strengths"
                elif key_word.startswith("weakness"):
                    current = "weaknesses"
                elif key_word.startswith("opportunit"):
                    current = "opportunities"
                elif key_word.startswith("threat"):
                    current = "threats"
                elif key_word.startswith("suggest"):
                    current = "suggestions"
                # ensure the section exists (already initialized)
                continue

            # If inside a section, extract bullets or whole line as an item
            if current:
                # Remove leading bullets, numbers, and typical markdown bold markers
                cleaned = re.sub(r"^[\-\*\•\d\.\)\s]+", "", line)   # remove - * • 1. 1) etc.
                cleaned = cleaned.replace("**", "").replace("*", "").strip()
                if cleaned:
                    sections[current].append(cleaned)

        logger.info(f"✅ Parsed SWOT sections (clean): {json.dumps(sections, indent=2)}")
        return sections



