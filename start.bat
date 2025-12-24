@echo off
title SmartCAPI Launcher
echo ============================================
echo      SmartCAPI Integrated Startup Script
echo ============================================
echo.

cd /d "%~dp0"

echo 1. Starting Redis Server...
start "Redis Server" redis-server

echo 2. Starting Backend API (Port 8001)...
start "SmartCAPI API" cmd /k "cd smartcapi-backend & call .venv\Scripts\activate & python run_server.py"

echo 3. Starting Hybrid Workers...
start "SmartCAPI Workers" cmd /k "cd smartcapi-backend & call .venv\Scripts\activate & python run_workers.py"

echo 4. Starting Frontend Client (Vite)...
start "SmartCAPI Client" cmd /k "cd smartcapi-client & npm run dev"

echo.
echo All services have been launched in separate windows.
echo - Client: http://localhost:5173 (usually)
echo - API: http://localhost:8001
echo - Workers: Active
echo.
pause
