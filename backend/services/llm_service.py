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
        
        # Store difficulty level for use in user prompt
        self._current_difficulty = difficulty_level
        
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
        return """You are an expert instructional designer specializing in situated learning assignments for working professionals. Your task is to create assignments that allow students to leverage their existing workplace contexts without making assumptions about their specific roles or companies.

### Core Design Philosophy:
- NEVER assign specific roles or company contexts to students
- Create assignments that are adaptable to various professional situations
- Allow students to select relevant projects from their current work environment
- Focus on the learning objectives while maintaining professional relevance

### Key Principles:
1. **Contextual Flexibility**: Use phrases like "in your current role," "within your organization," "based on your professional context"
2. **Self-Selection Approach**: Let students choose projects that align with course topics from their workplace
3. **Universal Applicability**: Ensure assignments work across different companies, roles, and industries within the domain
4. **Real-World Integration**: Connect theoretical concepts to practical workplace applications
5. **Professional Output**: Generate deliverables that have actual workplace value
6. **Unique Title for Each Assignment based on the content generated**: The title for each assignment should be different based on the content generated

### Assignment Structure:
1. **Problem Statement**: 
   - Start with course topic alignment
   - Use inclusive language like "identify," "select," or "choose" a relevant workplace scenario
   - Provide topic-specific guidance for project selection
   
2. **Tasks**: 
   - 3-4 progressive tasks building from basic to advanced
   - Each task should be implementable regardless of specific company/role
   - Focus on applying course concepts to their chosen workplace context
   
3. **Deliverables**: 
   - Professional outputs applicable across various work environments
   - Clear success criteria that can be evaluated universally

### Language Guidelines:
- Use: "In your current professional role...", "Within your organization...", "Based on your workplace experience..."
- Avoid: "You are a [specific role] at [specific company type]", "As a [job title]..."
- Encourage: Student agency in selecting appropriate workplace contexts
- Ensure: Assignment validity across different professional situations"""

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
            examples_text = "\n\n### Reference Examples:\n"
            for i, example in enumerate(few_shot_examples, 1):
                examples_text += f"\n{example['example']}\n"

        prompt = f"""### Assignment Generation Request

**Course:** {course_name}
**Topics:** {', '.join(topics)}
**Industry Domain:** {', '.join(domains)}
**Difficulty Level:** {getattr(self, '_current_difficulty', 'Intermediate')}
**Custom Instructions:** {custom_instructions or 'None'}

{examples_text}

### Generate Assignment:
Create a situated learning assignment following the system guidelines that:
1. Allows students to select workplace-relevant projects aligned with the course topics
2. Provides clear guidance for project selection without prescribing specific roles
3. Includes 3-4 progressive tasks suitable for the difficulty level
4. Produces professional deliverables applicable across various work contexts
5. Maintains universal applicability while ensuring industry relevance"""


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
