@echo off
cd /d "%~dp0..\.."

echo === Starting Portfolio Bot (Docker) ===
docker-compose up --build -d
echo Bot started in background.
pause
