@echo off
setlocal

:: Navigate to project root
cd /d "%~dp0..\.."

echo === Starting Portfolio Bot (Local) ===

if not exist ".venv" (
    echo Virtual environment not found. Please run scripts\windows\setup.bat first.
    pause
    exit /b 1
)

:: Activate venv
call .venv\Scripts\activate.bat

echo Starting Bot...
python -m src.bot
pause
