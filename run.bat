@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo HR Buddy - Resume Processing System
echo ============================================
echo.

if not exist "backend" (
    echo ERROR: backend directory not found!
    pause
    exit /b 1
)

echo [1/4] Checking Python environment...
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
    echo Using virtual environment (.venv)
) else (
    set PYTHON_EXE=python
    echo Using system Python (ensure all packages installed)
)

!PYTHON_EXE! --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo [2/4] Checking backend components...
if not exist "backend\main.py" (
    echo ERROR: backend\main.py not found!
    pause
    exit /b 1
)

echo [3/4] Cleaning up port 8002...
REM Kill any existing process on port 8002
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [4/4] Starting Backend API on port 8002...
echo Using Python: !PYTHON_EXE!
start "HR Buddy Backend" cmd /k "cd /d "%CD%" && !PYTHON_EXE! -u backend/main.py"

echo [5/5] Starting services...
echo.
echo Waiting for backend to initialize (this may take 30-60 seconds on first run)...
timeout /t 3 /nobreak

if exist "frontend" (
    echo Starting Frontend on port 3000...
    start "HR Buddy Frontend" cmd /k "cd /d "%CD%" && !PYTHON_EXE! -u -m http.server 3000 --directory frontend"
)

echo.
echo ============================================
echo Services Started!
echo ============================================
echo.
echo Backend API:    http://localhost:8002
echo API Docs:       http://localhost:8002/docs
echo Health Check:   http://localhost:8002/health
echo Frontend:       http://localhost:3000 (if available)
echo.
echo First API call may take 30-60 seconds (models load on demand)
echo Subsequent calls will be fast
echo.
echo Services are running in separate windows.
echo Check the windows that opened for status.
echo.
echo To test: !PYTHON_EXE! test_api.py
echo.
pause
