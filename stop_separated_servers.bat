@echo off
REM Stop all Situated Learning servers for local development

echo.
echo ========================================
echo   Situated Learning System - Shutdown
echo ========================================
echo.

echo 🛑 Stopping all Situated Learning servers...
echo.

REM Find and kill Python processes running our servers
echo 📤 Stopping Upload Server (Port 8020)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8020"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo 🎯 Stopping Generation Server (Port 8021)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8021"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo 🔍 Stopping Evaluation Server (Port 8022)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8022"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo 📊 Stopping Analytics Server (Port 8023)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8023"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo 👨‍🎓 Stopping Student Server (Port 8024)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8024"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo 👨‍🏫 Stopping Faculty Server (Port 8025)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8025"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

REM Check if Vite development server is running (frontend)
echo 🌐 Stopping Frontend Development Server (Port 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo.
echo ✅ All servers have been stopped.
echo.

pause