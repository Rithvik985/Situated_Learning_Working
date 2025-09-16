"""
LLM Service for Assignment Generation
"""

import os
import json
import requests
from typing import List, Dict, Optional
import logging
from config.settings import settings
from utils.llm_config import llm_config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.timeout = 480  # 8 minutes for LLM generation
        # Use the LLM configuration
        self.base_url = llm_config.text_model_url
        self.model_name = llm_config.text_model_name
        self.headers = llm_config.get_headers()

    async def generate_assignment(
        self,
        course_name: str,
        topics: List[str],
        domains: List[str],
        difficulty_level: str,
        custom_instructions: Optional[str] = None,
        few_shot_examples: List[Dict] = None
    ) -> str:
        """Generate a situated learning assignment using LLM"""
        
        system_prompt = self._create_system_prompt(difficulty_level)
        user_prompt = self._create_user_prompt(
            course_name, topics, domains, custom_instructions, few_shot_examples
        )
        
        try:
            response = await self._call_llm(system_prompt, user_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating assignment: {str(e)}")
            raise

    def _create_system_prompt(self, difficulty_level: str) -> str:
        """Create system prompt for assignment generation"""
        return f"""You are an expert instructional designer specializing in situated learning assignments for working professionals. Your task is to create assignments that reflect real workplace challenges and leverage students' existing job roles and experience.

Key Principles for Situated Learning Assignments:
1. Real-World Context: Use authentic problems or projects from the student's professional environment.
2. Workplace Integration: Ensure students can apply concepts, tools, and methods to tasks they are currently handling or could realistically encounter.
3. Data-Driven Design: Encourage use of workplace data where possible; if unavailable, allow online data with proper attribution.
4. Practical Implementation: Assignments should require designing, optimizing, simulating, or analyzing systems using actual technologies and industry standards.
5. Professional Deliverables: Assignments should produce outputs (reports, designs, diagrams, code) that are actionable in real projects.
6. Progressive Complexity: Structure tasks to build from guided applications to analysis and critical problem-solving.

Assignment Guidelines:
- Begin with a problem statement rooted in a real or plausible workplace scenario.
- Define the student's role and responsibilities clearly.
- Provide hardware/software/system requirements where applicable.
- Encourage use of tools, protocols, or data relevant to the industry domain.
- Include sections on design, implementation, testing, and reporting.
- Provide clear instructions on deliverables, success criteria, and documentation.

Difficulty Level Guidance:
- Beginner: Structured tasks with defined steps and templates.
- Intermediate: Analytical tasks requiring decision-making and partial guidance.
- Advanced: Open-ended problem-solving requiring innovation, optimization, and validation.

Output Format:
- Professional tone and clear language suitable for working professionals.
- Organized structure with numbered tasks, clear expectations, and deliverables.
- Guidance on how assignments connect theory with real-world applications."""

    def _create_user_prompt(
        self,
        course_name: str,
        topics: List[str],
        domains: List[str],
        custom_instructions: Optional[str],
        few_shot_examples: List[Dict]
    ) -> str:
        """Create user prompt with context and examples"""
        
        # Format few-shot examples
        examples_text = ""
        if few_shot_examples:
            examples_text = "\n\n### Reference Examples (for format and style guidance):\n"
            for i, example in enumerate(few_shot_examples, 1):
                examples_text += f"\n**Example {i} - {example['domain']}:**\n{example['example']}\n"

        prompt = f"""### Assignment Generation Context

**Course:** {course_name}
**Topics:** {', '.join(topics)}
**Industry Domains:** {', '.join(domains)}
"""

        if custom_instructions:
            prompt += f"**Custom Instructions:** {custom_instructions}\n"

        prompt += f"""
{examples_text}

### Task
Generate a NEW situated learning assignment that:

1. Creates a realistic problem statement based on the provided course, topics, and industry domains.
2. Aligns with the student's professional role and encourages use of workplace experience.
3. Incorporates data-driven and practical methods, allowing for hands-on implementation.
4. Includes 3–4 tasks that build from basic to advanced levels, suited to the assignment's difficulty level.
5. Provides actionable deliverables with clear reporting, simulation, or testing requirements.
6. Uses professional terminology and industry-standard tools or protocols.
7. Connects theoretical knowledge to workplace challenges with measurable outcomes."""

        return prompt

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to LLM"""
        try:
            # Log the complete prompt for verification
            logger.info("=" * 80)
            logger.info("LLM PROMPT DEBUG - SYSTEM PROMPT:")
            logger.info(system_prompt)
            logger.info("=" * 80)
            logger.info("LLM PROMPT DEBUG - USER PROMPT:")
            logger.info(user_prompt)
            logger.info("=" * 80)
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # Use synchronous requests for now, can be made async later
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {str(e)}")
            raise Exception(f"Failed to generate assignment: {str(e)}")
        except KeyError as e:
            logger.error(f"Unexpected LLM response format: {str(e)}")
            raise Exception(f"Invalid response from LLM: {str(e)}")
