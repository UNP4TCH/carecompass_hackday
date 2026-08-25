# CareCompass

**AI-powered first-step healthcare navigation — not diagnosis.**

CareCompass is a hackathon-ready prototype that turns an unstructured symptom description into a short, adaptive conversation and cautious next-step guidance.

## Core architecture

```text
User description
      ↓
Deterministic safety gate
      ↓
AI symptom understanding
      ↓
Adaptive next question
      ↓
User answer
      ↓
Safety re-check
      ↓
Case update + reassessment
      ↓
Adaptive next question OR final guidance
```

The **deterministic safety layer is independent of Gemini**. Gemini is used for language understanding, information extraction, adaptive question selection, and final non-diagnostic guidance.

## Features included

- React + Vite frontend
- FastAPI backend
- Gemini structured-output integration
- Adaptive follow-up questions
- Continuous reassessment after every valid answer
- Deterministic red-flag safety gate before AI processing
- New-symptom safety re-checks
- Maximum question/turn cap to prevent loops
- Structured final guidance with urgency and care level
- Emergency interruption UI
- AI-unavailable fail-safe state
- Backend unit/API/contract tests
- `.env.example` and setup scripts
- Architecture and AI workflow documentation

## Requirements

- Python 3.11+ recommended
- Node.js 20+ recommended
- A Gemini API key for live AI functionality

The app uses the Google GenAI Python SDK and a configurable Gemini model. The default model is `gemini-3.6-flash`; change `GEMINI_MODEL` in `backend/.env` if you want to use another supported model.

## 1. Backend setup

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and add your local key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

Run:

```powershell
uvicorn main:app --reload --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

## 2. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

If your backend is not on port 8000, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## 3. Tests

From `backend/` with the virtual environment active:

```bash
pytest -q
```

The adaptive contract test mocks the AI question selector, so it does not consume Gemini quota.

## 4. What the system deliberately does NOT claim

CareCompass does not:

- diagnose diseases
- replace doctors or emergency services
- guarantee medical accuracy
- prescribe medication or dosages
- make a definitive clinical triage decision from an LLM

Emergency language is screened by deterministic rules. If an emergency pattern is detected, the normal AI conversation is interrupted.

## 5. Project structure

```text
carecompass/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── pytest.ini
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── assessment_engine.py
│   │   ├── conversation_engine.py
│   │   ├── final_assessment.py
│   │   └── triage_engine.py
│   └── tests/
│       ├── test_api.py
│       ├── test_conversation_engine.py
│       ├── test_triage_engine.py
│       └── test_adaptive_contract.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
├── docs/
│   ├── architecture.md
│   ├── ai-workflow.md
│   └── demo-script.md
├── scripts/
│   ├── setup_windows.ps1
│   └── setup_unix.sh
└── README.md
```

## Important

Keep `backend/.env` local and never commit it. Only share `.env.example`.

This is a hackathon prototype, not a clinically validated medical device.
