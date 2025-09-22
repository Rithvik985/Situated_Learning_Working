#!/bin/bash
# Start all Situated Learning servers for local development
# This script starts all backend servers and the frontend

echo ""
echo "========================================"
echo "  Situated Learning System - Startup"
echo "========================================"
echo ""

# Check if .env file exists in backend directory
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env file not found!"
    echo "Please run: python setup_local_env.py"
    exit 1
fi

echo "🚀 Starting all Situated Learning servers..."
echo ""

# Function to start server in background
start_server() {
    local server_name="$1"
    local script_name="$2"
    local port="$3"
    
    echo "Starting $server_name (Port $port)..."
    nohup python "$script_name" > "logs/${server_name,,}.log" 2>&1 &
    local pid=$!
    echo "$pid" > "logs/${server_name,,}.pid"
    echo "✅ $server_name started (PID: $pid)"
    sleep 2
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Upload Server (Port 8020)
start_server "Upload Server" "start_upload_server.py" "8020"

# Start Generation Server (Port 8021)
start_server "Generation Server" "start_generation_server.py" "8021"

# Start Evaluation Server (Port 8022)
start_server "Evaluation Server" "start_evaluation_server.py" "8022"

# Start Analytics Server (Port 8023)
start_server "Analytics Server" "start_analytics_server.py" "8023"

# Start Frontend (Port 3000)
echo "🌐 Starting Frontend (Port 3000)..."
cd frontend
nohup npm run dev > "../logs/frontend.log" 2>&1 &
frontend_pid=$!
echo "$frontend_pid" > "../logs/frontend.pid"
echo "✅ Frontend started (PID: $frontend_pid)"
cd ..

echo ""
echo "✅ All servers started!"
echo ""
echo "📋 Server URLs:"
echo "  • Frontend:        http://localhost:3000"
echo "  • Upload API:      http://localhost:8020"
echo "  • Generation API:  http://localhost:8021"
echo "  • Evaluation API:  http://localhost:8022"
echo "  • Analytics API:   http://localhost:8023"
echo "  • MinIO Console:   http://localhost:9001 (admin/password1234)"
echo ""
echo "📁 Logs are saved in the 'logs/' directory"
echo "🛑 To stop all servers, run: ./stop_separated_servers.sh"
echo ""
