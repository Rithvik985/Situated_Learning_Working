#!/usr/bin/env python3
"""
Debug script to check LLM configuration
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def debug_environment():
    """Debug environment variables"""
    print("🔍 Environment Variables Debug:")
    print(f"USE_OPENAI: {os.getenv('USE_OPENAI', 'NOT SET')}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print(f"OPENAI_TEXT_MODEL: {os.getenv('OPENAI_TEXT_MODEL', 'NOT SET')}")
    print(f"OPENAI_VISION_MODEL: {os.getenv('OPENAI_VISION_MODEL', 'NOT SET')}")
    print(f"LLM_BASE_URL: {os.getenv('LLM_BASE_URL', 'NOT SET')}")
    print(f"LLM_MODEL_NAME: {os.getenv('LLM_MODEL_NAME', 'NOT SET')}")
    print()

def debug_llm_config():
    """Debug LLM configuration"""
    print("🔍 LLM Configuration Debug:")
    try:
        from utils.llm_config import llm_config
        
        config_info = llm_config.get_config_info()
        print(f"Provider: {config_info['provider']}")
        print(f"Text Model: {config_info['text_model']}")
        print(f"Vision Model: {config_info['vision_model']}")
        print(f"Text URL: {config_info['text_url']}")
        print(f"Vision URL: {config_info['vision_url']}")
        print(f"Has API Key: {config_info['has_api_key']}")
        print(f"Use OpenAI: {llm_config.use_openai}")
        print()
        
        return llm_config
    except Exception as e:
        print(f"❌ Error loading LLM config: {e}")
        return None

def debug_services():
    """Debug service configurations"""
    print("🔍 Service Configuration Debug:")
    try:
        from services.llm_service import LLMService
        # from services.rubric_service import RubricService
        
        llm_service = LLMService()
        print(f"LLM Service - Base URL: {llm_service.base_url}")
        print(f"LLM Service - Model: {llm_service.model_name}")
        print(f"LLM Service - Headers: {llm_service.headers}")
        print()
        
        # rubric_service = RubricService()
        # print(f"Rubric Service - Base URL: {rubric_service.base_url}")
        # print(f"Rubric Service - Model: {rubric_service.model_name}")
        # print(f"Rubric Service - Headers: {rubric_service.headers}")
        # print()
        
    except Exception as e:
        print(f"❌ Error loading services: {e}")

def main():
    """Main debug function"""
    print("🚀 LLM Configuration Debug Tool\n")
    
    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"✅ Found .env file: {env_file}")
    else:
        print(f"❌ No .env file found at: {env_file}")
        print("   Make sure to create a .env file with your configuration")
    
    print()
    
    # Debug environment variables
    debug_environment()
    
    # Debug LLM configuration
    llm_config = debug_llm_config()
    
    # Debug services
    debug_services()
    
    # Final recommendations
    print("📋 Recommendations:")
    if not os.getenv('USE_OPENAI'):
        print("1. Set USE_OPENAI=true in your .env file")
    if not os.getenv('OPENAI_API_KEY'):
        print("2. Set OPENAI_API_KEY in your .env file")
    if llm_config and not llm_config.use_openai:
        print("3. The system is configured to use vLLM instead of OpenAI")
        print("   Make sure USE_OPENAI=true is set in your environment")

if __name__ == "__main__":
    main()
