@echo off
setlocal

:: Navigate to project root
cd /d "%~dp0..\.."

echo === Portfolio Bot Setup (Windows) ===

:: 1. Check Poetry
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Poetry not found. Please install Poetry manually or via:
    echo "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"
    pause
    exit /b 1
)

:: 2. Configure Poetry
echo Configuring Poetry...
poetry config virtualenvs.in-project true

:: 3. Install Dependencies
echo Installing dependencies...
poetry install --no-root

:: 4. Setup .env
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo .env file created! Please edit it with your real API keys.
) else (
    echo .env file already exists.
)

echo === Setup Complete! ===
echo To run the bot locally, use: scripts\windows\run.bat
echo To run with Docker, use: scripts\windows\docker_run.bat
pause
