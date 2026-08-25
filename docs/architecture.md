# CareCompass Architecture

## System layers

### 1. Frontend
React/Vite provides:
- symptom intake
- conversational UI
- progress state
- emergency interruption
- structured result presentation

### 2. API
FastAPI exposes:
- `POST /api/conversation/start`
- `POST /api/conversation/answer`
- `DELETE /api/conversation/{conversation_id}`
- `GET /health`

### 3. Assessment engine
The assessment engine orchestrates the entire lifecycle and keeps the safety layer authoritative.

### 4. Deterministic safety layer
`triage_engine.py` performs a conservative first-pass phrase screen. It runs before AI processing and again when answers reveal new information.

### 5. AI reasoning layer
`ai_service.py` uses structured Gemini output for:
- symptom extraction
- answer interpretation
- adaptive next-question selection
- final non-diagnostic guidance

### 6. Conversation state
The current prototype stores sessions in memory for hackathon simplicity. A database can replace the dictionary in `main.py` without changing the assessment contract.

## Key invariant

> The LLM can reason about language, but it cannot override a deterministic emergency interruption.

## Production evolution

A production version would require clinical validation, formal safety engineering, secure persistent storage, authentication, privacy controls, auditability, monitoring, and professional medical governance.
