"""
AI Text Detection Service using RADAR (Robust AI-Text Detection via Adversarial Learning)
"""
from typing import Dict, Any, List
import logging
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class RadarService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.detector = AutoModelForSequenceClassification.from_pretrained("TrustSafeAI/RADAR-Vicuna-7B")
            self.tokenizer = AutoTokenizer.from_pretrained("TrustSafeAI/RADAR-Vicuna-7B")
            self.detector.eval()
            self.detector.to(self.device)
        except Exception as e:
            logger.error(f"Failed to initialize RADAR model: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize AI detection model")

    async def detect_ai_content(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to determine probability of AI generation
        
        Args:
            text: The text content to analyze
            
        Returns:
            Dict containing AI probability and analysis details
        """
        try:
            with torch.no_grad():
                inputs = self.tokenizer([text], padding=True, truncation=True, 
                                      max_length=512, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                output_probs = F.log_softmax(self.detector(**inputs).logits, -1)[:, 0].exp().tolist()

            # Get the probability for the text
            ai_prob = output_probs[0]

            return {
                "ai_probability": ai_prob,
                "is_likely_ai": ai_prob > 0.8,  # Threshold can be adjusted
                "confidence_score": ai_prob if ai_prob > 0.5 else (1 - ai_prob),
                "analysis_details": {
                    "raw_probability": ai_prob,
                    "model_name": "RADAR-Vicuna-7B",
                    "threshold": 0.8
                }
            }
        except Exception as e:
            logger.error(f"Error during AI detection: {str(e)}")
            raise HTTPException(status_code=500, detail="AI detection analysis failed")

    async def analyze_submission(self, submission_content: str) -> Dict[str, Any]:
        """
        Analyze a student submission for AI-generated content
        
        Args:
            submission_content: The text content of the submission
            
        Returns:
            Dict containing analysis results and recommendations
        """
        # Get AI detection results
        detection_results = await self.detect_ai_content(submission_content)

        # Generate detailed analysis report
        report = {
            "ai_detection_results": detection_results,
            "risk_assessment": self._assess_risk(detection_results["ai_probability"]),
            "recommendations": self._generate_recommendations(detection_results["ai_probability"]),
            "submission_stats": {
                "text_length": len(submission_content),
                "word_count": len(submission_content.split())
            }
        }

        return report

    def _assess_risk(self, ai_probability: float) -> Dict[str, Any]:
        """Assess the risk level based on AI probability"""
        if ai_probability > 0.9:
            risk_level = "High"
            risk_score = 3
        elif ai_probability > 0.7:
            risk_level = "Medium"
            risk_score = 2
        else:
            risk_level = "Low"
            risk_score = 1

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "explanation": f"The submission has a {risk_level.lower()} risk of being AI-generated based on RADAR analysis."
        }

    def _generate_recommendations(self, ai_probability: float) -> List[str]:
        """Generate recommendations based on AI probability"""
        recommendations = []
        
        if ai_probability > 0.9:
            recommendations.extend([
                "Request student to explain their work in detail",
                "Compare with previous submissions to identify pattern changes",
                "Consider requesting a revised submission with cited sources"
            ])
        elif ai_probability > 0.7:
            recommendations.extend([
                "Review submission more carefully",
                "Look for inconsistencies in writing style",
                "Consider discussing with student about academic integrity"
            ])
        else:
            recommendations.extend([
                "Normal review process recommended",
                "Document AI check results for future reference"
            ])

        return recommendations