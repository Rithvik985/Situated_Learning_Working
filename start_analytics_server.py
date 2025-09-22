#!/usr/bin/env python3
"""
Analytics Server for Situated Learning System
Handles all analytics and reporting queries
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set environment variables for analytics server
os.environ.setdefault("SERVER_TYPE", "analytics")
os.environ.setdefault("PORT", "8023")

def main():
    """Start the analytics server"""
    print("🚀 Starting Situated Learning Analytics Server...")
    print("📊 Port: 8023")
    print("🔗 Endpoints: http://localhost:8023/analytics/")
    print("📚 Docs: http://localhost:8023/docs")
    print("=" * 50)
    
    # Import and configure the analytics app
    from servers.analytics_server import app
    
    # Start the server
    uvicorn.run(
        "servers.analytics_server:app",
        host="0.0.0.0",
        port=8023,
        reload=True,
        reload_dirs=["backend"],
        log_level="info"
    )

if __name__ == "__main__":
    main()
