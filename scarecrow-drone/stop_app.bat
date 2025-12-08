@echo off
echo ========================================
echo    Scarecrow Drone - Stopping App
echo ========================================
echo.

:: Find and kill process on port 5000 (Backend)
echo Stopping Backend (port 5000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 echo   Backend stopped (PID: %%a)
)

:: Find and kill process on port 3000 (Frontend)
echo Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 echo   Frontend stopped (PID: %%a)
)

echo.
echo ========================================
echo    App stopped
echo ========================================
pause
