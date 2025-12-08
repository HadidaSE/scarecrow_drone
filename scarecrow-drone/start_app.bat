@echo off
echo ========================================
echo    Scarecrow Drone - Starting App
echo ========================================
echo.

:: Get the directory where the batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ========================================
:: CHECK PYTHON
:: ========================================
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo       Python found.

:: ========================================
:: CHECK NODE.JS
:: ========================================
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo       Node.js found.

:: ========================================
:: CHECK/CREATE BACKEND VENV
:: ========================================
echo [3/6] Checking backend virtual environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo       Creating virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    cd ..
    echo       Virtual environment created.
) else (
    echo       Virtual environment exists.
)

:: ========================================
:: INSTALL BACKEND DEPENDENCIES
:: ========================================
echo [4/6] Checking backend dependencies...
cd backend
.\venv\Scripts\pip install -q -r requirements.txt 2>nul
if errorlevel 1 (
    echo       Installing backend dependencies...
    .\venv\Scripts\pip install fastapi uvicorn paramiko
)
cd ..
echo       Backend dependencies ready.

:: ========================================
:: INSTALL FRONTEND DEPENDENCIES
:: ========================================
echo [5/6] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo       Installing frontend dependencies (this may take a minute)...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd ..
    echo       Frontend dependencies installed.
) else (
    echo       Frontend dependencies exist.
)

:: ========================================
:: START SERVERS
:: ========================================
echo [6/6] Starting servers...
echo.

:: Start Backend in new window
echo Starting Backend (FastAPI) on port 5000...
start "Scarecrow Backend" cmd /k "cd /d %SCRIPT_DIR%backend && .\venv\Scripts\python.exe -m uvicorn app:app --reload --port 5000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend in new window
echo Starting Frontend (React) on port 3000...
start "Scarecrow Frontend" cmd /k "cd /d %SCRIPT_DIR%frontend && npm start"

echo.
echo ========================================
echo    Both servers starting...
echo ========================================
echo.
echo    Backend:  http://localhost:5000
echo    Frontend: http://localhost:3000
echo.
echo    Close the terminal windows to stop.
echo    Or run stop_app.bat to stop both.
echo ========================================
pause
