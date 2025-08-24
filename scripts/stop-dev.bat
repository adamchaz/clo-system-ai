@echo off
echo 🛑 Stopping CLO Development Environment...

taskkill /f /im node.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

cd infrastructure\docker
docker-compose down

echo ✅ Development environment stopped