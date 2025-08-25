@echo off
echo 🚀 Starting Gutter Estimation App...

REM Check if .env file exists
if not exist "backend\.env" (
    echo ❌ .env file not found in backend directory!
    echo Please copy env.example to backend\.env and add your API keys
    pause
    exit /b 1
)

echo 🔧 Starting FastAPI backend...
start "Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo 🎨 Starting React frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo ✅ Services started!
echo 📱 Frontend: http://localhost:3000
echo 🔌 Backend: http://localhost:8000
echo 📊 API Docs: http://localhost:8000/docs
echo.
echo Close the command windows to stop the services
pause
