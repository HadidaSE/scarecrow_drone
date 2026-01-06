@echo off
echo ========================================
echo    Scarecrow Drone - Starting App
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ========================================
:: CHECK PYTHON
:: ========================================
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo       Python found.

:: ========================================
:: CHECK NODE.JS
:: ========================================
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)
echo       Node.js found.

:: ========================================
:: SETUP BACKEND
:: ========================================
echo [3/4] Setting up backend...
cd backend

if not exist venv (
    echo       Creating virtual environment...
    python -m venv venv
)

echo       Installing/updating dependencies...
call venv\Scripts\pip.exe install -r requirements.txt >nul 2>&1

cd ..
echo       Backend ready.

:: ========================================
:: SETUP FRONTEND
:: ========================================
echo [4/4] Setting up frontend...
cd frontend

if not exist node_modules (
    echo       Installing node modules - this may take a few minutes...
    call npm install
)

cd ..
echo       Frontend ready.

:: ========================================
:: START SERVERS
:: ========================================
echo.
echo ========================================
echo    Starting servers...
echo ========================================
echo.

echo Starting Backend on port 5000...
start "Scarecrow Backend" cmd /k "cd /d "%SCRIPT_DIR%backend" && venv\Scripts\python.exe -m uvicorn app:app --reload --port 5000"

timeout /t 3 /nobreak >nul

echo Starting Frontend on port 3000...
start "Scarecrow Frontend" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm start"

echo.
echo ========================================
echo    Servers starting...
echo ========================================
echo.
echo    Backend:  http://localhost:5000
echo    Frontend: http://localhost:3000
echo.
echo    Close the terminal windows to stop.
echo ========================================
echo.
pause
