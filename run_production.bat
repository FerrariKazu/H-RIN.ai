@echo off
echo ===================================================
echo   HR BUDDY PRODUCTION LAUNCHER
echo ===================================================

REM 1. Start Backend (Port 8001)
echo [1/3] Starting FASTAPI Backend (Port 8001)...
start "HR Buddy Backend" cmd /k "python backend/main.py"

REM 2. Start Frontend (Port 3001 via Vite)
echo [2/3] Starting Vite Frontend (Port 3001)...
cd frontend
start "HR Buddy Frontend" cmd /k "npm run dev"
cd ..

REM 3. Optional Ngrok Info
echo [3/3] To expose publicly, run: ngrok http 8001
echo.
echo ===================================================
echo   SYSTEM IS STARTING...
echo   Backend: http://localhost:8001
echo   Frontend: http://localhost:3001
echo ===================================================
pause
