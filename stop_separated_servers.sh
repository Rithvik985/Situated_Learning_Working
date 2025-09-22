#!/bin/bash
# Stop all Situated Learning servers

echo ""
echo "🛑 Stopping all Situated Learning servers..."
echo ""

# Function to stop server
stop_server() {
    local server_name="$1"
    local pid_file="logs/${server_name,,}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Stopping $server_name (PID: $pid)..."
            kill "$pid"
            echo "✅ $server_name stopped"
        else
            echo "⚠️  $server_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file found for $server_name"
    fi
}

# Stop all servers
stop_server "upload"
stop_server "generation"
stop_server "evaluation"
stop_server "analytics"
stop_server "frontend"

echo ""
echo "✅ All servers stopped!"
echo ""
