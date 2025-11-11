#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import uvicorn
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Add the project root to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    # Run the student server
    uvicorn.run(
        "backend.servers.student_server:app",
        host="0.0.0.0",
        port=8024,
        reload=True,
        log_level="info"
    )