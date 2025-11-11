"""
Evaluation Server for Situated Learning System
Handles student submission evaluation, scoring, and assessment functionality
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to Python path to access backend modules
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import routers and configuration
from routers.evaluation import router as evaluation_router
from routers.student import router as student_router
from routers.faculty import router as faculty_router
from database.connection import init_db
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('evaluation_server.log')  # Also log to file
    ]
)

# Disable noisy third-party loggers
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

# Get our application logger
app_logger = logging.getLogger('evaluation_server')
app_logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Evaluation Server...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't fail startup, just log the error
    
    yield
    
    logger.info("Shutting down Evaluation Server...")

# Create FastAPI application
app = FastAPI(
    title="Situated Learning - Evaluation Server",
    description="Student submission evaluation and assessment API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(evaluation_router, prefix="/evaluation")
app.include_router(student_router, prefix="/student")
app.include_router(faculty_router, prefix="/faculty")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "evaluation"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Situated Learning - Evaluation Server",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("EVALUATION_PORT", 8022))  # Evaluation server port
    logger.info(f"Starting Evaluation Server on port {port}")
    uvicorn.run(
        "evaluation_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
