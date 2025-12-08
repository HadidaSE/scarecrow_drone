@echo off
echo ========================================
echo    Scarecrow Drone - Starting App
echo ========================================
echo.

:: Start Backend in new window
echo Starting Backend (FastAPI) on port 5000...
start "Scarecrow Backend" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn app:app --reload --port 5000"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend in new window
echo Starting Frontend (React) on port 3000...
start "Scarecrow Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ========================================
echo    Both servers starting...
echo ========================================
echo.
echo    Backend:  http://localhost:5000
echo    Frontend: http://localhost:3000
echo.
echo    Close the terminal windows to stop.
echo ========================================
