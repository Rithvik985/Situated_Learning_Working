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

# Situated Learning Rubric Definition
# Situated Learning Rubric Definition
SITUATED_LEARNING_RUBRIC = {
    "name": "Situated_Learning_Rubric",
    "dimensions": [
        {
            "name": "Workplace Context Analysis",
            "criteria_output": {
                "Situational Assessment": {
                    "Score 4": "Provides comprehensive, insightful analysis of workplace context with relevant details",
                    "Score 3": "Clearly describes workplace context with sufficient detail to frame the application",
                    "Score 2": "Basic description of workplace context with some gaps in relevant details",
                    "Score 1": "Vague or insufficient description of workplace context"
                },
                "Stakeholder Consideration": {
                    "Score 4": "Thoroughly analyzes how solution impacts various stakeholders with specific insights",
                    "Score 3": "Identifies relevant stakeholders and considers how solution affects them",
                    "Score 2": "Limited consideration of stakeholders and their needs",
                    "Score 1": "Minimal or no consideration of stakeholders"
                },
                "Organizational Constraints": {
                    "Score 4": "Sophisticated analysis of organizational constraints with creative approaches to navigate limitations",
                    "Score 3": "Identifies relevant constraints and adapts solution accordingly",
                    "Score 2": "Acknowledges some constraints but with limited adaptation",
                    "Score 1": "Fails to identify significant constraints that impact implementation"
                }
            }
        },
        {
            "name": "Solution Development and Implementation",
            "criteria_output": {
                "Solution Viability": {
                    "Score 4": "Develops innovative, practical solution with clear implementation path",
                    "Score 3": "Proposes realistic solution with reasonable implementation considerations",
                    "Score 2": "Solution has some practical elements but implementation path is unclear",
                    "Score 1": "Solution is impractical or disconnected from workplace realities"
                },
                "Technical Accuracy": {
                    "Score 4": "Solution demonstrates mastery of technical aspects with no errors",
                    "Score 3": "Solution is technically sound with minor errors that don't impact effectiveness",
                    "Score 2": "Some technical misunderstandings that partially affect solution quality",
                    "Score 1": "Significant technical errors that undermine solution viability"
                },
                "Resource Utilization": {
                    "Score 4": "Optimizes available resources with creative leveraging of existing systems",
                    "Score 3": "Appropriately utilizes available resources with reasonable efficiency",
                    "Score 2": "Identifies necessary resources but utilization plan has inefficiencies",
                    "Score 1": "Inadequate consideration of resource requirements"
                }
            }
        },
        {
            "name": "Critical Reflection and Learning",
            "criteria_output": {
                "Self-Assessment": {
                    "Score 4": "Demonstrates exceptional insight into personal learning with specific examples",
                    "Score 3": "Accurately assesses strengths and limitations of approach with examples",
                    "Score 2": "Basic self-assessment with limited examples",
                    "Score 1": "Superficial or absent self-assessment"
                },
                "Alternative Approaches": {
                    "Score 4": "Thoroughly examines alternative approaches with sophisticated analysis of trade-offs",
                    "Score 3": "Identifies viable alternatives and discusses their relative merits",
                    "Score 2": "Limited exploration of alternatives with superficial analysis",
                    "Score 1": "Minimal or no consideration of alternative approaches"
                },
                "Lessons for Future Application": {
                    "Score 4": "Articulates specific, actionable insights for future applications with depth",
                    "Score 3": "Identifies meaningful lessons for future scenarios",
                    "Score 2": "Basic lessons identified with limited specificity",
                    "Score 1": "Few or no meaningful lessons articulated"
                }
            }
        },
        {
            "name": "Communication and Documentation",
            "criteria_output": {
                "Clarity and Organization": {
                    "Score 4": "Exceptionally clear, logically organized with professional presentation",
                    "Score 3": "Clear, well-organized with appropriate structure",
                    "Score 2": "Generally understandable but with some organizational issues",
                    "Score 1": "Difficult to follow with significant organizational problems"
                },
                "Technical Language": {
                    "Score 4": "Precise use of technical terminology with sophisticated industry-appropriate language",
                    "Score 3": "Accurate use of technical terminology appropriate to the field",
                    "Score 2": "Generally correct terminology with occasional misuse",
                    "Score 1": "Frequent misuse of technical terminology"
                },
                "Supporting Evidence": {
                    "Score 4": "Comprehensive evidence with excellent integration of workplace data",
                    "Score 3": "Sufficient relevant evidence to support claims",
                    "Score 2": "Limited evidence with some relevance to claims",
                    "Score 1": "Minimal or irrelevant evidence"
                }
            }
        },
        {
            "name": "Professional Impact and Value",
            "criteria_output": {
                "Workplace Value": {
                    "Score 4": "Solution offers significant potential value with specific benefits to organization",
                    "Score 3": "Solution provides clear value to workplace with identifiable benefits",
                    "Score 2": "Solution offers some value but benefits are limited or vague",
                    "Score 1": "Limited or no clear value to workplace"
                },
                "Sustainability": {
                    "Score 4": "Thoroughly addresses long-term sustainability with implementation plan",
                    "Score 3": "Considers sustainability factors with reasonable maintenance approach",
                    "Score 2": "Limited consideration of sustainability factors",
                    "Score 1": "No consideration of long-term sustainability"
                },
                "Knowledge Transfer": {
                    "Score 4": "Demonstrates exceptional ability to translate academic knowledge to workplace with potential to influence others",
                    "Score 3": "Effectively transfers academic knowledge to workplace context",
                    "Score 2": "Basic transfer of knowledge with limited influence",
                    "Score 1": "Minimal evidence of knowledge transfer"
                }
            }
        }
    ]
}

@dataclass
class EvaluationResult:
    """Data class to store evaluation results for each question"""
    category: str
    question: str
    score: int  # 1-4 scale per rubric
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
    overall_score: float  # Out of 72
    total_criteria: int   # Total number of evaluation criteria
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
        if False:
            self.client = OpenAI(
                api_key=llm_config.openai_api_key
            )
        else:
            # For vLLM, use the base URL without /chat/completions suffix
            vllm_base_url = llm_config.text_model_url.replace('/chat/completions', '')
            self.client = OpenAI(
                base_url=os.getenv("LLM_BASE_URL", vllm_base_url),
                api_key=os.getenv("LLM_API_KEY", "73a03f5d-59b3-4ef2-8bb72aed4a51")  # vLLM doesn't require real API keys
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
        # Format rubric for prompt
        rubric_text = "RUBRIC (Situated_Learning_Rubric):\n"
        for dimension in SITUATED_LEARNING_RUBRIC["dimensions"]:
            rubric_text += f"\n{dimension['name']}:\n"
            for criterion, scores in dimension['criteria_output'].items():
                rubric_text += f"\nCriterion: {criterion}\n"
                rubric_text += "Score Descriptors:\n"
                for score, description in scores.items():
                    rubric_text += f"  - {score}: {description}\n"

        prompt = f"""
You are an academic evaluator specializing in situated learning assessment. 
You will evaluate a student submission using the following structured rubric:

{rubric_text}

ASSIGNMENT DESCRIPTION:
{assignment_description}

STUDENT SUBMISSION:
{submission_text}

EVALUATION TARGET:
You must evaluate the submission against the following rubric dimension or specific sub-criterion:
{question}  # e.g. "Conceptual Understanding and Application > Depth of Application"

EVALUATION PROCESS:
1. The evaluation target shows which dimension and specific criterion to evaluate (e.g., "Conceptual Understanding > Depth of Application").
2. Find this specific criterion in the rubric and review its scoring descriptors.
3. Compare the student's submission against the performance levels described in the rubric (Score 4 through Score 1).
4. Choose the score that best matches the performance level descriptors.
5. Justify your score by citing specific evidence from the submission.

STRICT OUTPUT FORMAT:
SCORE: [1-4]  # Must be a whole number matching the rubric's score levels
REASONING: [2-3 sentences citing specific evidence from the submission and referencing the rubric descriptors]

Example:
SCORE: 3
REASONING: The submission demonstrates effective application of theoretical concepts to the workplace scenario, showing clear adaptation of course principles to practical situations (Score 3 descriptor). While the application is appropriate and contextual, it lacks the sophisticated integration and nuanced understanding required for Score 4.
"""

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
            
            # Ensure score is within bounds and is a whole number
            score = max(1, min(4, round(score)))  # Force whole number between 1-4
            
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
            Complete evaluation result with raw scores (out of 72 total points)
        """
        start_time = time.time()
        
        try:
            # Get rubric structure from SITUATED_LEARNING_RUBRIC
            dimensions = SITUATED_LEARNING_RUBRIC['dimensions']
            total_criteria = sum(len(dimension['criteria_output']) for dimension in dimensions)
            total_possible_score = total_criteria * 4  # Each criterion worth 4 points (72 total)
            
            logger.info(f"Starting evaluation of submission {submission_id}")
            logger.info(f"Rubric has {len(dimensions)} dimensions with {total_criteria} total criteria")
            logger.info(f"Total possible raw score: {total_possible_score} points (18 criteria × 4 points)")
            
            criterion_evaluations = []
            
            # Evaluate each dimension and its criteria
            for dimension_index, dimension in enumerate(dimensions, 1):
                dimension_name = dimension['name']
                criteria = dimension['criteria_output']
                logger.info(f"Evaluating dimension {dimension_index}/{len(dimensions)}: {dimension_name}")
                
                # Evaluate all criteria in this dimension
                criterion_results = []
                dimension_total_score = 0
                
                for criterion_name, criterion_scores in criteria.items():
                    logger.info(f"  Evaluating criterion: {criterion_name}")
                    
                    score, reasoning = self.evaluate_question(
                        assignment_description, submission_text, f"{dimension_name} > {criterion_name}"
                    )
                    
                    result = EvaluationResult(
                        category=dimension_name,
                        question=criterion_name,
                        score=score,
                        reasoning=reasoning
                    )
                    criterion_results.append(result)
                    dimension_total_score += score
                    
                    # Brief pause to avoid rate limiting
                    time.sleep(0.2)
                
                # Calculate dimension scores
                dimension_max_score = len(criteria) * 4  # Each criterion max is 4
                dimension_percentage = (dimension_total_score / dimension_max_score) * 100 if dimension_max_score > 0 else 0
                
                # Generate dimension-specific feedback
                dimension_feedback = self.generate_criterion_feedback(
                    dimension_name, criterion_results, dimension_percentage, assignment_description
                )
                
                dimension_eval = CriterionEvaluation(
                    category=dimension_name,
                    score=dimension_total_score,
                    max_score=dimension_max_score,
                    percentage=dimension_percentage,
                    feedback=dimension_feedback,
                    question_results=criterion_results
                )
                criterion_evaluations.append(dimension_eval)
                
                logger.info(f"  {dimension_name}: {dimension_total_score}/{dimension_max_score} ({dimension_percentage:.1f}%)")
            
            # Calculate overall scores (raw sum of all criterion scores)
            total_raw_score = sum(ce.score for ce in criterion_evaluations)
            
            # No normalization - use raw score out of 72
            final_score = round(total_raw_score, 2)
            
            # Log detailed scoring information
            logger.info(f"=== Detailed Evaluation Scores for {submission_id} ===")
            logger.info(f"Raw total score: {total_raw_score}")
            logger.info(f"Final score: {final_score}/72")
            logger.info("Individual criterion scores:")
            for ce in criterion_evaluations:
                logger.info(f"- {ce.category}: {ce.score}/{ce.max_score} ({ce.percentage:.1f}%)")
            
            # Generate overall feedback using raw score
            overall_feedback = self.generate_overall_feedback(criterion_evaluations, final_score)
            
            processing_time = time.time() - start_time
            
            # Create evaluation metadata with detailed dimension info
            evaluation_metadata = {
                'total_raw_score': total_raw_score,
                'total_possible_score': total_possible_score,
                'dimensions_count': len(dimensions),
                'criteria_per_dimension': [len(dim['criteria_output']) for dim in dimensions],
                'model_used': self.model,
                'evaluation_timestamp': time.time(),
                'dimension_details': [
                    {
                        'name': ce.category,
                        'score': ce.score,
                        'max_score': ce.max_score,
                        'percentage': ce.percentage
                    }
                    for ce in criterion_evaluations
                ]
            }
            
            evaluation = SubmissionEvaluation(
                submission_id=submission_id,
                overall_score=final_score,
                total_criteria=total_criteria,
                criterion_evaluations=criterion_evaluations,
                overall_feedback=overall_feedback,
                processing_time=processing_time,
                evaluation_metadata=evaluation_metadata
            )
            
            logger.info("SubmissionEvaluation object created successfully")
            logger.info(f"Completed evaluation of submission {submission_id} in {processing_time:.2f}s")
            logger.info(f"Final score: {final_score}/72 ({(final_score/72)*100:.1f}%)")
            
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
            criterion_scores = [f"{q.question}: {q.score}/4" for q in question_results]
            scores_summary = " | ".join(criterion_scores)
            feedback_points.append(f"**{performance_level} ({scores_summary})**: {category_name} demonstrates {performance_level.lower()} understanding.")
            
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
    
    def generate_overall_feedback(self, criterion_evaluations: List[CriterionEvaluation], raw_score: float) -> str:
        """
        Generate overall feedback summarizing performance across all criteria
        
        Args:
            criterion_evaluations: List of criterion evaluation results
            raw_score: Overall raw score out of 72 points
            
        Returns:
            Overall feedback text
        """
        try:
            percentage = (raw_score / 72) * 100  # Score out of 72 possible points
            
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
            
            logger.info(f"Generating overall feedback:")
            logger.info(f"Raw score: {raw_score}/72")
            logger.info(f"Percentage: {percentage:.1f}%")
            logger.info(f"Performance level: {performance_level}")
            
            # Identify strongest and weakest criteria
            sorted_criteria = sorted(criterion_evaluations, key=lambda x: x.percentage, reverse=True)
            strongest_criterion = sorted_criteria[0] if sorted_criteria else None
            weakest_criterion = sorted_criteria[-1] if sorted_criteria else None
            
            feedback_parts = []
            
            # Overall performance summary
            feedback_parts.append(f"**Overall Performance**: {performance_level} ({raw_score:.1f}/72, {percentage:.0f}%) - Your submission demonstrates {performance_description} of situated learning principles.")

            # Highlight strongest area
            if strongest_criterion and strongest_criterion.percentage >= 70:
                feedback_parts.append(f"**Key Strength**: {strongest_criterion.category} shows strong performance ({strongest_criterion.percentage:.0f}%), indicating good mastery of this area.")
            
            # Highlight area needing most attention
            if weakest_criterion and weakest_criterion.percentage < 70:
                feedback_parts.append(f"**Priority Focus**: {weakest_criterion.category} requires attention ({weakest_criterion.percentage:.0f}%) to strengthen overall performance.")            # Professional development note
            feedback_parts.append("**Professional Development**: Continue building connections between theoretical concepts and real-world applications to enhance your situated learning outcomes.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"Error generating overall feedback: {e}")
            return f"**Overall Performance**: Score of {raw_score:.1f}/72 ({(raw_score/72*100):.0f}%). Review detailed criterion feedback for specific improvement areas."
    
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
