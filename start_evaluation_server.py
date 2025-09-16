#!/usr/bin/env python3
"""
Start the Evaluation Server for Situated Learning System
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def start_evaluation_server():
    """Start the evaluation server"""
    backend_dir = Path(__file__).parent / "backend"
    server_script = backend_dir / "servers" / "evaluation_server.py"
    
    print("Starting Evaluation Server...")
    print(f"Server script: {server_script}")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(backend_dir)
    env['EVALUATION_PORT'] = '8019'
    
    try:
        # Start the server
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            env=env,
            cwd=str(backend_dir)
        )
        
        print(f"Evaluation Server started with PID: {process.pid}")
        print("Server running at: http://localhost:8019")
        print("API Documentation: http://localhost:8019/docs")
        print("Press Ctrl+C to stop the server")
        
        # Wait for process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping Evaluation Server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Evaluation Server stopped.")
    except Exception as e:
        print(f"Error starting evaluation server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = start_evaluation_server()
    sys.exit(exit_code)
