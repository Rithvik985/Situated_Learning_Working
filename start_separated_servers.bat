@echo off
REM Start all Situated Learning servers for local development
REM This script starts all backend servers and the frontend

echo.
echo ========================================
echo   Situated Learning System - Startup
echo ========================================
echo.

REM Check if .env file exists in backend directory
if not exist "backend\.env" (
    echo ❌ backend\.env file not found!
    echo Please run: python setup_local_env.py
    pause
    exit /b 1
)

echo 🚀 Starting all Situated Learning servers...
echo.

REM Start Upload Server (Port 8020)
echo 📤 Starting Upload Server (Port 8020)...
start "Upload Server" cmd /k "cd /d %~dp0 && python start_upload_server.py"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Generation Server (Port 8021)
echo 🎯 Starting Generation Server (Port 8021)...
start "Generation Server" cmd /k "cd /d %~dp0 && python start_generation_server.py"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Evaluation Server (Port 8022)
echo 🔍 Starting Evaluation Server (Port 8022)...
start "Evaluation Server" cmd /k "cd /d %~dp0 && python start_evaluation_server.py"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Analytics Server (Port 8023)
echo 📊 Starting Analytics Server (Port 8023)...
start "Analytics Server" cmd /k "cd /d %~dp0 && python start_analytics_server.py"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Frontend (Port 3000)
echo 🌐 Starting Frontend (Port 3000)...
start "Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ✅ All servers started!
echo.
echo 📋 Server URLs:
echo   • Frontend:        http://localhost:3000
echo   • Upload API:      http://localhost:8020
echo   • Generation API:  http://localhost:8021
echo   • Evaluation API:  http://localhost:8022
echo   • Analytics API:   http://localhost:8023
echo   • MinIO Console:   http://localhost:9001 (admin/password1234)
echo.
echo 💡 Each server runs in its own terminal window
echo 💡 Close individual terminals to stop specific servers
echo 💡 Press any key to close this startup window...
pause > nul
