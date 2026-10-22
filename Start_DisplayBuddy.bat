@echo off
setlocal enabledelayedexpansion
title Starting Display Buddy...

echo ========================================================
echo        Starting Display Buddy Desktop Companion...
echo ========================================================

cd /d "%~dp0"

:: 1. Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python is not installed or not in your PATH.
        echo Opening Python download page in your browser...
        start https://www.python.org/downloads/
        echo Please install Python (be sure to check "Add Python to PATH"!) and run this again.
        pause
        exit /b 1
    )
    set PY_CMD=py
) else (
    set PY_CMD=python
)

:: 2. Set up virtual environment if missing
if not exist ".venv\Scripts\pythonw.exe" (
    echo [Setup] First time running! Creating local environment (.venv)...
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [Setup] Installing dependencies (PyQt6)...
    .venv\Scripts\pip.exe install --quiet -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
    echo [Setup] Setup complete!
)

:: 3. Launch silently in the background (no black terminal window)
echo [Launch] Display Buddy is waking up on your taskbar! ✨
start "" ".venv\Scripts\pythonw.exe" main.py

exit /b 0
