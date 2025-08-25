@echo off
setlocal enabledelayedexpansion

REM 🏠 Gutter Estimate Pro - Service Startup Script (Windows)
REM This script starts both the backend API and frontend React app

title Gutter Estimate Pro - Service Manager

echo.
echo 🏠 Gutter Estimate Pro - Service Startup
echo ========================================
echo.

REM Check prerequisites
echo [INFO] Checking prerequisites...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.7+ first.
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo [SUCCESS] All prerequisites are met

REM Check if we're in the right directory
if not exist "backend" (
    echo [ERROR] Please run this script from the root directory (gutter_estimate^)
    pause
    exit /b 1
)

if not exist "frontend" (
    echo [ERROR] Please run this script from the root directory (gutter_estimate^)
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    if not exist ".venv" (
        echo [WARNING] Virtual environment not found. Creating one...
        python -m venv venv
        call venv\Scripts\activate.bat
        echo [INFO] Installing backend dependencies...
        pip install -r backend\requirements.txt
    ) else (
        call .venv\Scripts\activate.bat
    )
) else (
    call venv\Scripts\activate.bat
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo [WARNING] Frontend dependencies not found. Installing...
    cd frontend
    npm install
    cd ..
)

REM Kill any existing processes on our ports
echo [INFO] Checking for existing processes...

REM Kill processes on port 8000 (backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM Kill processes on port 3000 (frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo [INFO] Starting backend API server...

REM Start backend
cd backend
start "Backend API" cmd /k "python main.py"
cd ..

REM Wait for backend to start
echo [INFO] Waiting for backend to be ready...
timeout /t 10 /nobreak >nul

REM Check if backend is running
:check_backend
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% neq 0 (
    echo -n .
    timeout /t 2 /nobreak >nul
    goto check_backend
)

echo.
echo [SUCCESS] Backend is ready!

echo [INFO] Starting frontend React app...

REM Start frontend
cd frontend
start "Frontend App" cmd /k "npm start"
cd ..

REM Wait for frontend to start
echo [INFO] Waiting for frontend to be ready...
timeout /t 15 /nobreak >nul

REM Check if frontend is running
:check_frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo -n .
    timeout /t 2 /nobreak >nul
    goto check_frontend
)

echo.
echo.
echo 🎉 All services are running successfully!
echo.
echo Services:
echo   🔧 Backend API:  http://localhost:8000
echo   📚 API Docs:     http://localhost:8000/docs
echo   🎨 Frontend App: http://localhost:3000
echo.
echo To stop all services: Close the command windows or press Ctrl+C in each
echo.
echo Press any key to open the frontend in your browser...
pause >nul

REM Open frontend in default browser
start http://localhost:3000

echo.
echo [INFO] Frontend opened in browser. Keep this window open to monitor services.
echo [INFO] Press any key to stop all services...
pause >nul

REM Stop services
echo [INFO] Stopping services...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

echo [SUCCESS] All services stopped
pause
