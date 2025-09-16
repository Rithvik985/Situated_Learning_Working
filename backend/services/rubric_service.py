"""
Rubric Service for generating assignment rubrics
Integrated directly without external microservice dependency
"""

import os
import json
import requests
from typing import Dict, Optional
import logging
from config.settings import settings
from utils.llm_config import llm_config

logger = logging.getLogger(__name__)

class RubricService:
    def __init__(self):
        self.timeout = 480  # 8 minutes for LLM generation
        # Use the LLM configuration
        self.base_url = llm_config.text_model_url
        self.model_name = llm_config.text_model_name
        self.headers = llm_config.get_headers()

    async def generate_rubric(self, text: str, doc_type: str = "Situated Learning Assignment") -> Dict:
        """Generate rubric directly using LLM"""
        return await self._generate_rubric_direct(text, doc_type)

    async def _generate_rubric_direct(self, text: str, doc_type: str) -> Dict:
        """Generate rubric directly using LLM"""
        try:
            system_prompt = """You are an expert rubric designer for academic and industry-aligned assignments. Your task is to create an objective, measurable evaluation rubric that allows faculty to accurately assess student submissions based on defined criteria.

Instructions:
- Create exactly 4 rubric categories that cover the most important dimensions for evaluating the given assignment.
- Under each rubric category, write exactly 5 evaluation questions.
- Each question must be phrased to allow a measurable response — preferably yes/no, or countable observations — and avoid ambiguous or subjective phrasing.
- Do not use vague adjectives like "good", "appropriate", or "clear"; instead, frame criteria around observable actions, deliverables, or quantifiable performance.
- Ensure that the 4 categories and their 20 questions comprehensively assess the assignment's objectives, scope, methodology, implementation, and outcomes.
- Focus on how the student's work reflects understanding, application, problem-solving, and results relevant to the assignment's context.
- Avoid duplication between questions; each question should target a distinct aspect of evaluation.
- Where possible, align questions with the technical, procedural, or analytical requirements outlined in the assignment content.
- Your rubric should guide faculty to provide consistent, fair, and evidence-based evaluations across different student submissions.

Return STRICT JSON only in the format below. The JSON must not contain extra comments, explanations, or formatting errors:

{
  "rubric_name": str,
  "doc_type": str,
  "rubrics": [
    {
      "category": str,
      "questions": [str, str, str, str, str]
    },
    {
      "category": str,
      "questions": [str, str, str, str, str]
    },
    {
      "category": str,
      "questions": [str, str, str, str, str]
    },
    {
      "category": str,
      "questions": [str, str, str, str, str]
    }
  ]
}"""

            user_prompt = f"""Document type: {doc_type}

Assignment snippet (for tailoring criteria):
\"\"\"{text}\"\"\"

Now generate an evaluation rubric for this assignment."""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1500
            }
            
            # Log the complete prompt for verification
            logger.info("=" * 80)
            logger.info("RUBRIC GENERATION - SYSTEM PROMPT:")
            logger.info(system_prompt)
            logger.info("=" * 80)
            logger.info("RUBRIC GENERATION - USER PROMPT:")
            logger.info(user_prompt)
            logger.info("=" * 80)
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract content from LLM response
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response with multiple fallback strategies
            rubric_data = self._parse_json_response(content)
            
            # Ensure required fields exist
            rubric_data.setdefault("rubric_name", f"Objective Rubric for {doc_type.title()}")
            rubric_data.setdefault("doc_type", doc_type)
            
            logger.info(f"Generated rubric for {doc_type}: {rubric_data.get('rubric_name')}")
            return rubric_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise Exception(f"Failed to connect to LLM service: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise Exception(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Error in rubric generation: {str(e)}")
            # Return a basic rubric as final fallback
            return self._get_fallback_rubric(doc_type)

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response with multiple fallback strategies"""
        try:
            # Strategy 1: Direct JSON parsing
            return json.loads(content)
        except json.JSONDecodeError as e1:
            logger.warning(f"Direct JSON parsing failed: {e1}")
            
            try:
                # Strategy 2: Extract JSON from markdown code blocks
                import re
                json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
                matches = re.findall(json_pattern, content, re.DOTALL)
                if matches:
                    return json.loads(matches[0])
            except (json.JSONDecodeError, IndexError) as e2:
                logger.warning(f"Markdown extraction failed: {e2}")
            
            try:
                # Strategy 3: Find JSON object boundaries
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError as e3:
                logger.warning(f"Boundary extraction failed: {e3}")
            
            try:
                # Strategy 4: Clean and fix common JSON issues
                cleaned_content = self._clean_json_string(content)
                return json.loads(cleaned_content)
            except json.JSONDecodeError as e4:
                logger.warning(f"Cleaned JSON parsing failed: {e4}")
            
            # Strategy 5: Try to extract and reconstruct JSON
            try:
                return self._reconstruct_json(content)
            except Exception as e5:
                logger.warning(f"JSON reconstruction failed: {e5}")
            
            # If all strategies fail, raise the original error
            raise json.JSONDecodeError(f"All JSON parsing strategies failed. Original error: {e1}", content, 0)

    def _clean_json_string(self, content: str) -> str:
        """Clean common JSON formatting issues"""
        import re
        
        # Remove markdown code block markers
        content = re.sub(r'```(?:json)?\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Remove any text before the first {
        start = content.find("{")
        if start > 0:
            content = content[start:]
        
        # Remove any text after the last }
        end = content.rfind("}")
        if end > 0:
            content = content[:end + 1]
        
        # Fix common trailing comma issues
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # Fix missing quotes around keys
        content = re.sub(r'(\w+):', r'"\1":', content)
        
        return content.strip()

    def _reconstruct_json(self, content: str) -> Dict:
        """Attempt to reconstruct JSON from malformed content"""
        import re
        
        # Extract rubric name
        rubric_name_match = re.search(r'"rubric_name":\s*"([^"]*)"', content)
        rubric_name = rubric_name_match.group(1) if rubric_name_match else "Generated Rubric"
        
        # Extract doc_type
        doc_type_match = re.search(r'"doc_type":\s*"([^"]*)"', content)
        doc_type = doc_type_match.group(1) if doc_type_match else "Assignment"
        
        # Extract rubrics array
        rubrics = []
        rubric_pattern = r'"category":\s*"([^"]*)"[^}]*"questions":\s*\[(.*?)\]'
        
        for match in re.finditer(rubric_pattern, content, re.DOTALL):
            category = match.group(1)
            questions_text = match.group(2)
            
            # Extract questions
            question_pattern = r'"([^"]*)"'
            questions = re.findall(question_pattern, questions_text)
            
            if len(questions) >= 3:  # Ensure we have at least 3 questions
                rubrics.append({
                    "category": category,
                    "questions": questions[:5]  # Limit to 5 questions max
                })
        
        # Ensure we have at least 4 rubrics
        while len(rubrics) < 4:
            rubrics.append({
                "category": f"Evaluation Criteria {len(rubrics) + 1}",
                "questions": [
                    "Does the submission meet basic requirements?",
                    "Is the content technically sound?",
                    "Are examples provided?",
                    "Is the presentation clear?",
                    "Are conclusions well-supported?"
                ]
            })
        
        return {
            "rubric_name": rubric_name,
            "doc_type": doc_type,
            "rubrics": rubrics[:4]  # Ensure exactly 4 rubrics
        }

    def _get_fallback_rubric(self, doc_type: str) -> Dict:
        """Provide a basic fallback rubric if all generation methods fail"""
        return {
            "rubric_name": f"Basic Rubric for {doc_type}",
            "doc_type": doc_type,
            "rubrics": [
                {
                    "category": "Content Quality",
                    "questions": [
                        "Does the submission address all required components?",
                        "Is the content technically accurate?",
                        "Are concepts explained clearly?",
                        "Is supporting evidence provided?",
                        "Are examples relevant and appropriate?"
                    ]
                },
                {
                    "category": "Problem Analysis",
                    "questions": [
                        "Is the problem clearly identified?",
                        "Are assumptions explicitly stated?",
                        "Is the approach systematically organized?",
                        "Are alternative solutions considered?",
                        "Is the chosen solution justified?"
                    ]
                },
                {
                    "category": "Professional Application",
                    "questions": [
                        "Are industry standards referenced?",
                        "Is practical implementation addressed?",
                        "Are real-world constraints considered?",
                        "Is the solution scalable?",
                        "Are potential risks identified?"
                    ]
                },
                {
                    "category": "Communication & Presentation",
                    "questions": [
                        "Is the writing clear and professional?",
                        "Are ideas logically organized?",
                        "Are technical terms used appropriately?",
                        "Are conclusions well-supported?",
                        "Is the format professional and consistent?"
                    ]
                }
            ]
        }
