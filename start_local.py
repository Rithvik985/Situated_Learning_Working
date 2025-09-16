#!/usr/bin/env python3
"""
Local development startup script for Situated Learning System
"""

import os
import sys
import subprocess
import signal
import time
from threading import Thread

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.running = True
    
    def run_command(self, command, name, cwd=None):
        """Run a command in a separate process"""
        print(f"🚀 Starting {name}...")
        try:
            if sys.platform == "win32":
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    preexec_fn=os.setsid
                )
            
            self.processes.append((process, name))
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def start_backend(self):
        """Start the backend server"""
        if sys.platform == "win32":
            command = "backend\\venv\\Scripts\\python main.py"
        else:
            command = "backend/venv/bin/python main.py"
        
        return self.run_command(command, "Backend API", cwd="backend")
    
    def start_frontend(self):
        """Start the frontend development server"""
        return self.run_command("npm run dev", "Frontend Dev Server", cwd="frontend")
    
    def start_databases(self):
        """Start database services using Docker"""
        return self.run_command(
            "docker-compose up postgres minio redis",
            "Database Services"
        )
    
    def stop_all(self):
        """Stop all running processes"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for process, name in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"⏹️ Stopping {name}...")
                try:
                    if sys.platform == "win32":
                        process.terminate()
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        if sys.platform == "win32":
                            process.kill()
                        else:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        process.wait()
                    
                    print(f"✅ {name} stopped")
                except Exception as e:
                    print(f"❌ Error stopping {name}: {e}")
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            for process, name in self.processes:
                if process.poll() is not None:  # Process has exited
                    if self.running:
                        print(f"❌ {name} has stopped unexpectedly")
            time.sleep(2)
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n⚠️ Received signal {signum}")
        self.stop_all()
        sys.exit(0)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if backend virtual environment exists
    if sys.platform == "win32":
        venv_python = "backend\\venv\\Scripts\\python.exe"
    else:
        venv_python = "backend/venv/bin/python"
    
    if not os.path.exists(venv_python):
        print("❌ Backend virtual environment not found. Run setup.py first.")
        return False
    
    # Check if frontend node_modules exists
    if not os.path.exists("frontend/node_modules"):
        print("❌ Frontend dependencies not installed. Run setup.py first.")
        return False
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not accessible")
        return False
    
    print("✅ All prerequisites met")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Situated Learning System (Local Development)")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("README.md") or not os.path.exists("docker-compose.yml"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n💡 Run 'python setup.py' to set up the development environment")
        sys.exit(1)
    
    # Initialize service manager
    manager = ServiceManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # Start services
        print("\n📊 Starting database services...")
        db_process = manager.start_databases()
        if db_process:
            print("⏳ Waiting for databases to be ready...")
            time.sleep(10)
        
        print("\n🔧 Starting backend API...")
        backend_process = manager.start_backend()
        if backend_process:
            time.sleep(3)
        
        print("\n🎨 Starting frontend development server...")
        frontend_process = manager.start_frontend()
        
        # Print access information
        print("\n" + "=" * 60)
        print("🎉 All services started successfully!")
        print("\n📍 Access Points:")
        print("   • Frontend:     http://localhost:3000")
        print("   • Backend API:  http://localhost:8000")
        print("   • API Docs:     http://localhost:8000/docs")
        print("   • MinIO Console: http://localhost:9001 (admin/password1234)")
        print("\n⏹️ Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Start monitoring
        monitor_thread = Thread(target=manager.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep the main thread alive
        while manager.running:
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all()

if __name__ == "__main__":
    main()
