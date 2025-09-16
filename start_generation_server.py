#!/usr/bin/env python3
"""
Startup script for the Generation Server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the Generation Server"""
    
    # Get the directory of this script
    current_dir = Path(__file__).parent
    
    # Set environment variables for the server
    os.environ.setdefault("GENERATION_HOST", "0.0.0.0")
    os.environ.setdefault("GENERATION_PORT", "8017")
    
    # Add backend directory to Python path
    backend_dir = current_dir / "backend"
    sys.path.insert(0, str(backend_dir))
    
    print("🚀 Starting Generation Server...")
    print(f"📁 Working directory: {current_dir}")
    print(f"🔧 Backend path: {backend_dir}")
    print(f"🌐 Server will run on: http://localhost:{os.environ.get('GENERATION_PORT', '8017')}")
    print()
    
    # Change to the backend directory
    os.chdir(backend_dir)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "servers/generation_server.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Generation Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
