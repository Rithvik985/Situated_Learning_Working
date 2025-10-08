"""
Analytics Server for Situated Learning System
Dedicated server for analytics and reporting queries
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import sys
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent   # -> Situated_Learning
sys.path.insert(0, str(project_root))
from backend.database.connection import get_async_db
from backend.routers.analytics import router as analytics_router
from backend.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Situated Learning Analytics API",
    description="Analytics and reporting service for the Situated Learning System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include analytics router
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Situated Learning Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "analytics": "/api/analytics"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_async_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "service": "analytics",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "analytics",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("analytics_server:app", host="0.0.0.0", port=8023)
