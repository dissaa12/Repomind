# Repomind Launcher Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Repomind AI Codebase Intelligence System...    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start FastAPI Backend Server in a new window
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; .\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 127.0.0.1 --port 8000"

# 2. Start Vite React Frontend in a new window
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev"

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "[OK] Repomind is launching! Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"
