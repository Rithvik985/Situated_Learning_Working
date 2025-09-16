"""
Evaluation Service for scoring student submissions against rubrics
Enhanced version based on Situated_Learning_Final evaluation logic
"""

import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
import os
from config.settings import settings
from utils.llm_config import llm_config

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Data class to store evaluation results for each question"""
    category: str
    question: str
    score: int  # 0-5 scale
    reasoning: Optional[str] = None

@dataclass
class CriterionEvaluation:
    """Data class for criterion-wise evaluation results"""
    category: str
    score: float  # Normalized score for this criterion
    max_score: float  # Maximum possible score for this criterion
    percentage: float  # Percentage for this criterion
    feedback: str  # 4-6 point feedback for this criterion
    question_results: List[EvaluationResult]

@dataclass
class SubmissionEvaluation:
    """Complete evaluation result for a submission"""
    submission_id: str
    overall_score: float  # Out of 20
    total_questions: int
    criterion_evaluations: List[CriterionEvaluation]
    overall_feedback: str
    processing_time: float
    evaluation_metadata: Dict[str, Any]

class EvaluationService:
    """Enhanced service for evaluating student submissions using LLM and structured rubrics"""
    
    def __init__(self, timeout: int = 120):
        """
        Initialize the evaluation service using centralized LLM configuration
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        
        # Use centralized LLM configuration
        self.base_url = llm_config.text_model_url
        self.model = llm_config.text_model_name
        self.use_openai = llm_config.use_openai
        
        # Initialize OpenAI-compatible client
        if self.use_openai:
            self.client = OpenAI(
                api_key=llm_config.openai_api_key
            )
        else:
            # For vLLM, use the base URL without /chat/completions suffix
            vllm_base_url = llm_config.text_model_url.replace('/chat/completions', '')
            self.client = OpenAI(
                base_url=vllm_base_url,
                api_key="EMPTY"  # vLLM doesn't require real API keys
            )
        
        logger.info(f"Evaluation service initialized with {llm_config.get_config_info()['provider']} model: {self.model} at {self.base_url}")
    
    def create_evaluation_prompt(self, assignment_description: str, submission_text: str, question: str) -> str:
        """
        Create a comprehensive prompt for LLM evaluation with 0-5 scoring
        
        Args:
            assignment_description: The assignment requirements and context
            submission_text: Student's submission text
            question: Specific rubric question to evaluate
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are an expert academic evaluator specializing in situated learning assignments. Your task is to evaluate a student submission against a specific rubric criterion using a 5-point scale with detailed reasoning.

SITUATED LEARNING CONTEXT:
Situated learning assignments require students to apply theoretical knowledge to real-world scenarios, demonstrating practical understanding and professional application.

ASSIGNMENT DESCRIPTION:
{assignment_description}

STUDENT SUBMISSION:
{submission_text}

EVALUATION CRITERION:
{question}

SCORING SCALE (0-5):
5 - EXCELLENT: Exceeds expectations with comprehensive understanding, detailed analysis, strong evidence, and professional-level application
4 - GOOD: Meets expectations with solid understanding, adequate analysis, relevant evidence, and appropriate application
3 - SATISFACTORY: Basic understanding demonstrated with some analysis, limited evidence, and minimal application
2 - NEEDS IMPROVEMENT: Partial understanding with weak analysis, insufficient evidence, or unclear application
1 - POOR: Minimal understanding with little to no analysis, missing evidence, or inappropriate application
0 - MISSING: No evidence of addressing this criterion or completely incorrect response

EVALUATION INSTRUCTIONS:
1. Analyze the submission specifically for situated learning elements (real-world application, practical context, professional relevance)
2. Look for evidence of theoretical knowledge being applied to practical situations
3. Assess the quality of analysis, reasoning, and professional judgment demonstrated
4. Consider the depth of understanding shown through examples, calculations, or case applications
5. Evaluate the clarity and professionalism of communication
6. Be consistent and fair while maintaining academic rigor

RESPONSE FORMAT (STRICTLY FOLLOW):
SCORE: [0-5]
REASONING: [Provide 2-3 sentences explaining the score with specific evidence from the submission, focusing on what was done well and what could be improved]

Example response:
SCORE: 4
REASONING: The submission demonstrates solid understanding of energy audit principles with clear methodology and relevant calculations. The analysis includes practical considerations for implementation and shows good professional judgment. However, the cost-benefit analysis could be more detailed and the timeline for implementation needs more specificity."""

        return prompt
    
    def evaluate_question(self, assignment_description: str, submission_text: str, question: str, max_retries: int = 3) -> Tuple[int, str]:
        """
        Evaluate a single rubric question using LLM with 0-5 scoring
        
        Args:
            assignment_description: Assignment context
            submission_text: Student's submission
            question: Rubric question to evaluate
            max_retries: Maximum retry attempts
            
        Returns:
            Tuple of (score, reasoning)
        """
        prompt = self.create_evaluation_prompt(assignment_description, submission_text, question)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Evaluating question (attempt {attempt + 1}): {question[:50]}...")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a precise academic evaluator for situated learning assignments. Always follow the exact format: SCORE: [0-5] then REASONING: [2-3 sentences with specific evidence]."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1  # Low temperature for consistent evaluation
                )
                
                response_text = response.choices[0].message.content.strip()
                logger.debug(f"LLM response: {response_text}")
                
                # Parse response
                score, reasoning = self.parse_llm_response_new(response_text)
                
                if 0 <= score <= 5:
                    logger.debug(f"Question evaluated: Score {score}/5 - {reasoning}")
                    return score, reasoning
                else:
                    logger.warning(f"Invalid score in response: {response_text}. Retrying...")
                    
            except Exception as e:
                logger.error(f"Error during evaluation (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to evaluate question after {max_retries} attempts")
                    return 0, "Evaluation failed due to technical error"
                time.sleep(1)  # Brief pause before retry
        
        return 0, "Evaluation failed after multiple attempts"
    
    def parse_llm_response_new(self, response_text: str) -> Tuple[int, str]:
        """
        Parse LLM response to extract score and reasoning
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Tuple of (score, reasoning)
        """
        try:
            lines = response_text.split('\n')
            score = 0
            reasoning = "No reasoning provided"
            
            for line in lines:
                line = line.strip()
                if line.startswith("SCORE:"):
                    score_text = line.split(":", 1)[1].strip()
                    try:
                        score = int(score_text)
                    except ValueError:
                        # Try to extract number from text
                        import re
                        numbers = re.findall(r'\d+', score_text)
                        if numbers:
                            score = int(numbers[0])
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
            
            # Fallback parsing if format not followed exactly
            if not (0 <= score <= 5):
                import re
                # Look for any number in the response
                numbers = re.findall(r'\b[0-5]\b', response_text)
                if numbers:
                    score = int(numbers[0])
                else:
                    score = 0
                
                # Use entire response as reasoning if no proper format
                reasoning = response_text[:200] + ("..." if len(response_text) > 200 else "")
            
            # Ensure score is within bounds
            score = max(0, min(5, score))
            
            # Truncate reasoning if too long
            if len(reasoning) > 300:
                reasoning = reasoning[:297] + "..."
            
            return score, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return 0, "Error parsing response"
    
    def evaluate_submission(self, assignment_description: str, submission_text: str, rubric: Dict[str, Any], submission_id: str) -> SubmissionEvaluation:
        """
        Evaluate entire submission against rubric with flexible scoring
        
        Args:
            assignment_description: Assignment requirements and context
            submission_text: Complete student submission text
            rubric: Structured rubric with categories and questions
            submission_id: Unique identifier for the submission
            
        Returns:
            Complete evaluation result normalized to 20 points
        """
        start_time = time.time()
        
        try:
            # Get rubric structure
            criteria = rubric.get('rubrics', [])
            total_questions = sum(len(category['questions']) for category in criteria)
            total_possible_score = total_questions * 5  # Each question worth 5 points
            
            logger.info(f"Starting evaluation of submission {submission_id}")
            logger.info(f"Rubric has {len(criteria)} criteria with {total_questions} total questions")
            logger.info(f"Total possible raw score: {total_possible_score} points")
            
            criterion_evaluations = []
            
            # Evaluate each criterion
            for criterion_index, category in enumerate(criteria, 1):
                category_name = category['category']
                questions = category['questions']
                logger.info(f"Evaluating criterion {criterion_index}/{len(criteria)}: {category_name}")
                
                # Evaluate all questions in this criterion
                question_results = []
                category_total_score = 0
                
                for question_index, question in enumerate(questions, 1):
                    logger.info(f"  Question {question_index}/{len(questions)}: {question[:60]}...")
                    
                    score, reasoning = self.evaluate_question(
                        assignment_description, submission_text, question
                    )
                    
                    result = EvaluationResult(
                        category=category_name,
                        question=question,
                        score=score,
                        reasoning=reasoning
                    )
                    question_results.append(result)
                    category_total_score += score
                    
                    # Brief pause to avoid rate limiting
                    time.sleep(0.2)
                
                # Calculate criterion scores
                category_max_score = len(questions) * 5
                category_percentage = (category_total_score / category_max_score) * 100 if category_max_score > 0 else 0
                
                # Generate criterion-specific feedback
                criterion_feedback = self.generate_criterion_feedback(
                    category_name, question_results, category_percentage, assignment_description
                )
                
                criterion_eval = CriterionEvaluation(
                    category=category_name,
                    score=category_total_score,
                    max_score=category_max_score,
                    percentage=category_percentage,
                    feedback=criterion_feedback,
                    question_results=question_results
                )
                criterion_evaluations.append(criterion_eval)
                
                logger.info(f"  {category_name}: {category_total_score}/{category_max_score} ({category_percentage:.1f}%)")
            
            # Calculate overall scores
            total_raw_score = sum(ce.score for ce in criterion_evaluations)
            
            # Normalize to 20 points
            normalized_score = (total_raw_score / total_possible_score) * 20 if total_possible_score > 0 else 0
            normalized_score = round(normalized_score, 2)
            
            # Generate overall feedback
            overall_feedback = self.generate_overall_feedback(criterion_evaluations, normalized_score)
            
            processing_time = time.time() - start_time
            
            evaluation = SubmissionEvaluation(
                submission_id=submission_id,
                overall_score=normalized_score,
                total_questions=total_questions,
                criterion_evaluations=criterion_evaluations,
                overall_feedback=overall_feedback,
                processing_time=processing_time,
                evaluation_metadata={
                    'total_raw_score': total_raw_score,
                    'total_possible_score': total_possible_score,
                    'normalization_factor': 20 / total_possible_score if total_possible_score > 0 else 0,
                    'criteria_count': len(criteria),
                    'model_used': self.model,
                    'evaluation_timestamp': time.time()
                }
            )
            
            logger.info(f"Completed evaluation of submission {submission_id} in {processing_time:.2f}s")
            logger.info(f"Final score: {normalized_score}/20 ({(normalized_score/20)*100:.1f}%)")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating submission {submission_id}: {str(e)}")
            raise Exception(f"Evaluation failed: {str(e)}")
    
    def generate_criterion_feedback(self, category_name: str, question_results: List[EvaluationResult], 
                                  category_percentage: float, assignment_description: str) -> str:
        """
        Generate detailed feedback for a specific criterion with 4-6 points
        
        Args:
            category_name: Name of the criterion category
            question_results: Results for questions in this category
            category_percentage: Percentage score for this category
            assignment_description: Assignment context
            
        Returns:
            Structured feedback string with 4-6 points
        """
        try:
            # Analyze performance level
            if category_percentage >= 85:
                performance_level = "Excellent"
            elif category_percentage >= 70:
                performance_level = "Good"
            elif category_percentage >= 50:
                performance_level = "Satisfactory"
            else:
                performance_level = "Needs Improvement"
            
            # Get high and low scoring questions
            high_scores = [q for q in question_results if q.score >= 4]
            medium_scores = [q for q in question_results if 2 <= q.score < 4]
            low_scores = [q for q in question_results if q.score < 2]
            
            feedback_points = []
            
            # Point 1: Performance summary
            feedback_points.append(f"**{performance_level} Performance ({category_percentage:.0f}%)**: {category_name} demonstrates {performance_level.lower()} understanding with room for targeted improvements.")
            
            # Point 2: Strengths (if any high scores)
            if high_scores:
                strengths = []
                for result in high_scores[:2]:  # Limit to top 2 for brevity
                    if result.reasoning and len(result.reasoning) > 10:
                        strength_detail = result.reasoning.split('.')[0]  # First sentence
                        strengths.append(strength_detail.strip())
                if strengths:
                    feedback_points.append(f"**Key Strengths**: {' '.join(strengths[:2])}.")
            
            # Point 3: Areas needing attention (if any low scores)
            if low_scores:
                feedback_points.append(f"**Priority Areas**: {len(low_scores)} question(s) need significant improvement, particularly regarding practical application and detailed analysis.")
            
            # Point 4: Specific improvements (always include)
            if medium_scores or low_scores:
                improvement_areas = medium_scores + low_scores
                if improvement_areas:
                    feedback_points.append(f"**Improvement Focus**: Strengthen evidence presentation, provide more detailed explanations, and ensure all aspects of {category_name.lower()} are adequately addressed.")
            
            # Point 5: Professional context (for situated learning)
            feedback_points.append(f"**Professional Application**: Enhance real-world connections and demonstrate deeper understanding of how {category_name.lower()} applies in professional practice.")
            
            # Point 6: Next steps (if performance is not excellent)
            if category_percentage < 85:
                if category_percentage < 50:
                    feedback_points.append("**Next Steps**: Review fundamental concepts, seek additional resources, and practice applying theoretical knowledge to practical scenarios.")
                else:
                    feedback_points.append("**Next Steps**: Focus on providing more comprehensive analysis and stronger supporting evidence in future submissions.")
            
            # Join points with proper formatting
            return " ".join(feedback_points[:6])  # Limit to 6 points maximum
            
        except Exception as e:
            logger.error(f"Error generating criterion feedback: {e}")
            return f"**{category_name} Feedback**: Score of {category_percentage:.0f}% indicates {'good' if category_percentage >= 70 else 'developing'} performance. Focus on providing more detailed analysis and stronger evidence to improve in this area."
    
    def generate_overall_feedback(self, criterion_evaluations: List[CriterionEvaluation], normalized_score: float) -> str:
        """
        Generate overall feedback summarizing performance across all criteria
        
        Args:
            criterion_evaluations: List of criterion evaluation results
            normalized_score: Overall score normalized to 20 points
            
        Returns:
            Overall feedback text
        """
        try:
            percentage = (normalized_score / 20) * 100
            
            # Determine overall performance level
            if percentage >= 85:
                performance_level = "Excellent"
                performance_description = "exceptional understanding and application"
            elif percentage >= 70:
                performance_level = "Good" 
                performance_description = "solid understanding with effective application"
            elif percentage >= 50:
                performance_level = "Satisfactory"
                performance_description = "basic understanding with developing application skills"
            else:
                performance_level = "Needs Improvement"
                performance_description = "foundational gaps requiring focused development"
            
            # Identify strongest and weakest criteria
            sorted_criteria = sorted(criterion_evaluations, key=lambda x: x.percentage, reverse=True)
            strongest_criterion = sorted_criteria[0] if sorted_criteria else None
            weakest_criterion = sorted_criteria[-1] if sorted_criteria else None
            
            feedback_parts = []
            
            # Overall performance summary
            feedback_parts.append(f"**Overall Performance**: {performance_level} ({normalized_score:.1f}/20, {percentage:.0f}%) - Your submission demonstrates {performance_description} of situated learning principles.")
            
            # Highlight strongest area
            if strongest_criterion and strongest_criterion.percentage >= 70:
                feedback_parts.append(f"**Key Strength**: {strongest_criterion.category} shows strong performance ({strongest_criterion.percentage:.0f}%), indicating good mastery of this area.")
            
            # Highlight area needing most attention
            if weakest_criterion and weakest_criterion.percentage < 70:
                feedback_parts.append(f"**Priority Focus**: {weakest_criterion.category} requires attention ({weakest_criterion.percentage:.0f}%) to strengthen overall performance.")
            
            # Professional development note
            feedback_parts.append("**Professional Development**: Continue building connections between theoretical concepts and real-world applications to enhance your situated learning outcomes.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"Error generating overall feedback: {e}")
            return f"**Overall Performance**: Score of {normalized_score:.1f}/20 ({((normalized_score/20)*100):.0f}%). Review detailed criterion feedback for specific improvement areas."
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the LLM evaluation service
        
        Returns:
            Status dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Respond with 'Evaluation service test successful' if you can process this message."}
                ],
                max_tokens=20,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "message": "Evaluation service connection successful",
                "model": self.model,
                "response": content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "model": self.model
            }
