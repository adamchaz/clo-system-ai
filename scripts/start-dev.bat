@echo off
echo 🚀 Starting CLO Development Environment...

echo 📦 Starting Docker services...
cd infrastructure\docker
docker-compose up -d postgres redis

echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak > nul

echo 🐍 Starting Python backend...
cd ..\..\backend
call venv\Scripts\activate.bat
start /b uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo ⚛️ Starting React frontend...
cd ..\frontend
start /b npm start

echo ✅ Development environment started!
echo 📊 Frontend: http://localhost:3000
echo 🔗 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs

pause