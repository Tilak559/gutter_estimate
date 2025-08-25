@echo off
echo 🏠 Setting up Gutter Estimate Pro Frontend...
echo ==============================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    echo    Visit: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo ✅ Node.js and npm detected

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully!
) else (
    echo ❌ Failed to install dependencies. Please check the error above.
    pause
    exit /b 1
)

echo.
echo 🎉 Setup complete! You can now start the frontend:
echo.
echo    npm start
echo.
echo 📱 The frontend will be available at: http://localhost:3000
echo 🔗 Make sure your backend is running on: http://localhost:8000
echo.
echo 📚 For more information, see README.md
pause
