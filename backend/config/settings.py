"""
Configuration settings for Situated Learning System
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

class Settings:
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:password1234@localhost:5432/situated_learning_db")
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "password1234")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "situated-learning")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # LLM Configuration
    USE_OPENAI: bool = os.getenv("USE_OPENAI", "false").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    OPENAI_TEXT_MODEL: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    OPENAI_VISION_MODEL: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://172.16.26.22/vllm-llama3.3-gateway/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4")
    VISION_LLM_BASE_URL: str = os.getenv("VISION_LLM_BASE_URL", "http://172.16.26.22/vllm-vision-qwen2.5-gateway/v1")
    VISION_LLM_MODEL_NAME: str = os.getenv("VISION_LLM_MODEL_NAME", "Qwen/Qwen2.5-VL-32B-Instruct-AWQ")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY","73a03f5d-59b3-4ef2-8bb72aed4a51")
    VISION_LLM_API_KEY: str = os.getenv("VISION_LLM_API_KEY","73a03f5d-59b3-4ef2-8bb72aed4a51")

    # File Processing
    MAX_FILE_SIZE: str = os.getenv("MAX_FILE_SIZE", "50MB")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    
    # CORS Settings
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://frontend:3000,http://localhost:8080")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Redis Configuration (for caching and background tasks)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Assignment Generation Settings
    MAX_ASSIGNMENTS_PER_REQUEST: int = int(os.getenv("MAX_ASSIGNMENTS_PER_REQUEST", "10"))
    DEFAULT_CLASS_NUMBERS: str = os.getenv("DEFAULT_CLASS_NUMBERS", "4,7,10")
    
    # Evaluation Settings
    MAX_SUBMISSIONS_PER_EVALUATION: int = int(os.getenv("MAX_SUBMISSIONS_PER_EVALUATION", "5"))
    OCR_CONFIDENCE_THRESHOLD: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.8"))
    PLAGIARISM_THRESHOLD: float = float(os.getenv("PLAGIARISM_THRESHOLD", "0.7"))
    AI_DETECTION_THRESHOLD: float = float(os.getenv("AI_DETECTION_THRESHOLD", "0.6"))


# Global settings instance
settings = Settings()
