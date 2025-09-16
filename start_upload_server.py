#!/usr/bin/env python3
"""
Startup script for Upload Server only
"""

import os
import sys
import subprocess
import signal
import time

def run_upload_server():
    """Start the upload server"""
    print("Starting Upload Server for Situated Learning System")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("backend/servers/upload_server.py"):
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if virtual environment exists
    if sys.platform == "win32":
        venv_python = "backend\\venv\\Scripts\\python.exe"
    else:
        venv_python = "backend/venv/bin/python"
    
    if not os.path.exists(venv_python):
        print("ERROR: Backend virtual environment not found. Run setup.py first.")
        sys.exit(1)
    
    try:
        # Start upload server
        print("Starting Upload Server on port 8016...")
        cmd = [venv_python, "servers/upload_server.py"]
        
        process = subprocess.Popen(
            cmd,
            cwd="backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("Upload Server started successfully!")
        print("\nAccess Points:")
        print("   - Upload API:   http://localhost:8016")
        print("   - API Docs:     http://localhost:8016/docs")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping Upload Server...")
        if process:
            process.terminate()
            process.wait()
        print("Upload Server stopped")
    except Exception as e:
        print(f"Error starting Upload Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_upload_server()
