@echo off
echo Starting HR Buddy App...

:: Start Backend
start "HR Buddy Backend" cmd /k "python backend/main.py"

:: Start Frontend
start "HR Buddy Frontend" cmd /k "python -m http.server 3000 --directory frontend/src"

echo.
echo 🚀 Services Started!
echo --------------------------------------------
echo 🔙 Backend: http://localhost:8001
echo 🖥️ Frontend: http://localhost:3000
echo --------------------------------------------
echo.
echo Press any key to exit this launcher (services will keep running).
pause
