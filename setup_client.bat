@echo off
echo ========================================
echo ZAY POS - Client Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python 3.10 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b
)

:: Install required packages
echo Installing required packages...
pip install --upgrade pip
pip install --upgrade setuptools
pip install pkg_resources
pip install -r requirements.txt

:: Create necessary folders
echo Creating folders...
if not exist database mkdir database
if not exist logs mkdir logs
if not exist assets\icons mkdir assets\icons

:: Run the application
echo Starting application...
python main.py

pause