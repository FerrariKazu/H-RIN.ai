@echo off
REM Setup script to prepare the environment

echo ============================================
echo HR Buddy - Setup & Installation
echo ============================================
echo.

cd /d "%~dp0"

echo Step 1: Creating virtual environment (if not exists)...
if not exist venv (
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

echo.
echo Step 2: Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ✓ Dependencies installed

echo.
echo Step 3: Installing Spacy model...
python -m spacy download en_core_web_sm -q
echo ✓ Spacy model installed

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo To run the application:
echo   run.bat
echo.
pause
