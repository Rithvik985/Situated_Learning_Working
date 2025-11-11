import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import student
from routers import student_upload
import uvicorn

app = FastAPI(title="Student Service API")

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(student.router, prefix="/api/student", tags=["student"])
app.include_router(student_upload.router, prefix="/api/student", tags=["student"])

# Error handler for custom error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "success": False,
        "message": str(exc.detail),
        "status_code": exc.status_code
    }

# Include the student router
app.include_router(student.router, prefix="/api/student", tags=["student"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "student-server"}

if __name__ == "__main__":
    uvicorn.run("student_server:app", host="0.0.0.0", port=8024, reload=True)