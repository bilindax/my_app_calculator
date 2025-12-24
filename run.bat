@echo off
echo ========================================
echo   BILIND AutoCAD Extension Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if requirements are installed
echo Checking dependencies...
pip show pyautocad >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed
echo.
echo Starting BILIND Enhanced...
echo Make sure AutoCAD is running!
echo.

python bilind_main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Program crashed!
    pause
)
