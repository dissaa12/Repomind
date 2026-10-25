@echo off
title Repomind Codebase Intelligence
echo ==========================================================
echo   Starting Repomind AI Codebase Intelligence System...
echo ==========================================================

start "Repomind Backend (Port 8000)" cmd /k "cd /d ""%~dp0backend"" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
start "Repomind Frontend (Port 5173)" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

timeout /t 3 >nul
start http://localhost:5173
echo [OK] Repomind running! Browser opened to http://localhost:5173
