#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../backend"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Backend ready. Add GEMINI_API_KEY to backend/.env, then run: .venv/bin/python -m uvicorn main:app --reload --port 8000"
