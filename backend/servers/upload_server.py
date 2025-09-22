#!/usr/bin/env python3
"""
Upload Server for Situated Learning System
Handles past assignment uploads and processing
"""

import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database.connection import database, init_db
from storage.minio_client import minio_client
from routers.upload import router as upload_router
from config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        await database.connect()
        print("Database connected successfully")
        
        # Initialize MinIO connection
        minio_client.initialize_connection()
        print("MinIO connection initialized")
        
        # Initialize database tables
        await init_db()
        print("Database tables initialized")
        
    except Exception as e:
        print(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    await database.disconnect()
    print("Upload server shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Situated Learning - Upload Service",
    description="Upload and processing service for past assignments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include upload router
app.include_router(upload_router, prefix="/uploadAss")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Upload Service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Situated Learning Upload Service",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    port = 8020  # Upload server port
    print(f"Starting Upload Server on port {port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    
    uvicorn.run(
        "upload_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
