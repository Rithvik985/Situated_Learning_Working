"""
Generation Server for Situated Learning System
Handles assignment generation, rubric creation, and related functionality
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
from routers.generation import router as generation_router
from database.connection import init_db
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Generation Server...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't fail startup, just log the error
    
    yield
    
    logger.info("Shutting down Generation Server...")

# Create FastAPI application
app = FastAPI(
    title="Situated Learning - Generation Server",
    description="Assignment generation, rubric creation, and document management",
    version="1.0.0",
    lifespan=lifespan
)

# Configure request timeout (in seconds)
app.state.timeout = 600  # 10 minutes

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    generation_router, 
    prefix="/api/generation", 
    tags=["Assignment Generation"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "generation-server"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Situated Learning - Generation Server",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    # Server configuration
    host = os.getenv("GENERATION_HOST", "0.0.0.0")
    port = int(os.getenv("GENERATION_PORT", "8017"))
    
    logger.info(f"Starting Generation Server on {host}:{port}")
    
    uvicorn.run(
        "generation_server:app",
        host=host,
        port=port,
        reload=True,  # Enable for development
        log_level="info"
    )
