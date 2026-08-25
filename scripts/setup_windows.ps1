$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Backend ready. Add GEMINI_API_KEY to backend/.env, then run: .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
