#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import uvicorn

# Add the project root to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    # Run the faculty server
    uvicorn.run(
        "backend.servers.faculty_server:app",
        host="0.0.0.0",
        port=8025,
        reload=True,
        log_level="info"
    )