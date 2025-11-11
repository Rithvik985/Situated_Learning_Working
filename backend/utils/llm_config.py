"""
LLM Configuration Helper
Manages switching between OpenAI and vLLM configurations
"""
import os
from typing import Dict, Any
from config.settings import settings
api_key="73a03f5d-59b3-4ef2-8bb72aed4a51"

class LLMConfig:
    """Configuration manager for LLM services"""
    
    def __init__(self):
        # Use settings from pydantic-settings which loads from .env
        self.use_openai = settings.USE_OPENAI
        self.openai_api_key = settings.OPENAI_API_KEY
        
        if self.use_openai:
            self._setup_openai_config()
        else:
            self._setup_vllm_config()
    
    def _setup_openai_config(self):
        """Setup OpenAI configuration"""
        self.text_model_url = "https://api.openai.com/v1/chat/completions"
        self.text_model_name = settings.OPENAI_TEXT_MODEL
        self.vision_model_url = "https://api.openai.com/v1/chat/completions"
        self.vision_model_name = settings.OPENAI_VISION_MODEL
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when USE_OPENAI=true")
    
    def _setup_vllm_config(self):
        """Setup vLLM configuration"""
        # Use settings from pydantic-settings
        llm_base_url = settings.LLM_BASE_URL
        vision_llm_base_url = settings.VISION_LLM_BASE_URL
        
        # Get model names from settings
        text_model_name = settings.LLM_MODEL_NAME
        vision_model_name = settings.VISION_LLM_MODEL_NAME
        
        # Construct full URLs
        self.text_model_url = f"{llm_base_url}/chat/completions"
        self.text_model_name = text_model_name
        self.vision_model_url = f"{vision_llm_base_url}/chat/completions"
        self.vision_model_name = vision_model_name
    
    # def get_headers(self) -> Dict[str, str]:
    #     """Get appropriate headers for API calls"""
    #     headers = {
    #         "Content-Type": "application/json",

    #     }
        
    #     if self.use_openai and self.openai_api_key:
    #         headers["Authorization"] = f"Bearer {self.openai_api_key}"
        
    #     return headers
    def get_headers(self, is_vision: bool = False) -> Dict[str, str]:
        """
        Get appropriate headers for API calls.
        - If using OpenAI → Always use OPENAI_API_KEY
        - If using vLLM → Use separate API keys for text and vision models
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization":f"Bearer {api_key}"
        }

        # if self.use_openai:
        #     if not self.openai_api_key:
        #         raise ValueError("OPENAI_API_KEY is required when USE_OPENAI=true")
        #     headers["Authorization"] = f"Bearer {self.openai_api_key}"
        # else:
        #     # Use different API keys for text vs vision
        #     if is_vision:
        #         api_key = settings.VISION_LLM_API_KEY
        #     else:
        #         api_key = settings.LLM_API_KEY

        #     if not api_key:
        #         raise ValueError("Missing API key for LLM service")

        #     headers["Authorization"] = f"Bearer {api_key}"

        return headers


    
    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information"""
        return {
            "provider": "OpenAI" if self.use_openai else "vLLM",
            "text_model": self.text_model_name,
            "vision_model": self.vision_model_name,
            "text_url": self.text_model_url,
            "vision_url": self.vision_model_url,
            "has_api_key": bool(self.openai_api_key) if self.use_openai else True
        }
    
    def validate_config(self) -> bool:
        """Validate the current configuration"""
        if self.use_openai:
            return bool(self.openai_api_key)
        else:
            # For vLLM, we assume local services are running
            return True

# Global configuration instance
llm_config = LLMConfig()
