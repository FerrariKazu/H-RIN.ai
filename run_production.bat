@echo off
echo ===================================================
echo   HR BUDDY PRODUCTION LAUNCHER
echo ===================================================

REM 1. Start Ollama (Port 11500)
echo [1/4] Starting Ollama LLM Server (Port 11500)...
set OLLAMA_HOST=127.0.0.1:11500
start "Ollama Server" cmd /k "ollama serve"
timeout /t 5 /nobreak >nul

REM 2. Start Backend (Port 8001)
echo [2/4] Starting FASTAPI Backend (Port 8001)...
start "HR Buddy Backend" cmd /k "python backend/main.py"

REM 3. Start Frontend (Port 3001 via Vite)
echo [3/4] Starting Vite Frontend (Port 3001)...
cd frontend
start "HR Buddy Frontend" cmd /k "npm run dev"
cd ..

REM 4. Optional Ngrok Info
echo [4/4] To expose publicly, run: ngrok http 8001
echo.
echo ===================================================
echo   SYSTEM IS STARTING...
echo   Backend: http://localhost:8001
echo   Frontend: http://localhost:3001
echo ===================================================
pause
