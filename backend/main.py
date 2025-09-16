#!/usr/bin/env python3
"""
Situated Learning System - Main FastAPI Application
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config.settings import settings
from database.connection import database, init_db
from storage.minio_client import minio_client
from routers import upload, generation, evaluation, analytics

# Global instances are imported

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    try:
        await database.connect()
        print("✅ Database connected successfully")
        
        # Initialize MinIO connection
        minio_client.initialize_connection()
        print("✅ MinIO connection initialized")
        
        # Initialize database tables
        await init_db()
        print("✅ Database tables initialized")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    await database.disconnect()
    print("📴 Database disconnected")

# Create FastAPI application
app = FastAPI(
    title="Situated Learning System",
    description="AI-powered assignment generation and evaluation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(generation.router, prefix="/api/generation", tags=["Assignment Generation"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Situated Learning System",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Situated Learning System API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
