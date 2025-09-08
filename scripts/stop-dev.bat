@echo off
echo 🛑 Stopping CLO Development Environment...

REM Stop React frontend (port 3000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a > nul 2>&1

REM Stop FastAPI backend (port 8000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a > nul 2>&1

REM Stop Docker services
cd infrastructure\docker
docker-compose down

echo ✅ Development environment stopped