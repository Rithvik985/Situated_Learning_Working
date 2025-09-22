@echo off
REM Setup database and MinIO for Situated Learning System

echo.
echo ========================================
echo   Situated Learning Database Setup
echo ========================================
echo.

echo 🗄️ Starting PostgreSQL and MinIO containers...
docker-compose up postgres minio -d

echo.
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak > nul

echo.
echo 🔧 Initializing database structure...
python setup_database.py

echo.
echo ✅ Database setup complete!
echo.
echo 📋 Access Information:
echo   • PostgreSQL: localhost:5432 (admin/password1234)
echo   • MinIO Console: http://localhost:9001 (admin/password1234)
echo   • Database: situated_learning_db
echo.
echo 💡 You can now start the application with:
echo   .\start_separated_servers.bat
echo.
pause
