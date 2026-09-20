# CareCompass Architecture

*Updated: September 20, 2026 — Hackday 1.0 Submission*

## System Overview

CareCompass combines deterministic safety-first clinical routing with generative AI language understanding to bridge the gap between noticing a symptom or receiving complex paperwork and knowing the safest next action.

```text
+-------------------------------------------------------------------------+
|                              Frontend (React)                           |
|  - IntakeView: Free-text symptom input                                  |
|  - AssessmentView: Adaptive turn-by-turn question flow                  |
|  - EmergencyView: Red warning banner + 1-click nearby ER maps           |
|  - ResultView: Cautious guidance, timeline & Find Nearest Care          |
|  - CareSummaryDocument: Print-ready clinical summary (window.print)     |
|  - DocumentSimplifierView: Prescription & discharge note photo analysis |
+-------------------------------------------------------------------------+
                                    │
                         HTTP REST API (FastAPI)
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                       Backend Orchestration Layer                       |
|  - main.py: API endpoints, validation, CORS, rate-limit interception   |
|  - conversation_engine.py: Session state & message history              |
|  - assessment_engine.py: Assessment lifecycle orchestration             |
+-------------------------------------------------------------------------+
         │                                               │
         ▼                                               ▼
+--------------------------------+              +-------------------------+
|   Deterministic Safety Layer   |              |   Document Simplifier   |
| - triage_engine.py             |              | - document_service.py   |
| - Regex & pattern matcher      |              | - Pillow image verify   |
| - Negation & history filter    |              | - Gemini multimodal     |
| - Immediate interrupt gate     |              | - Safety disclaimers    |
+--------------------------------+              +-------------------------+
         │
         ▼
+-------------------------------------------------------------------------+
|                        AI Reasoning Layer (Gemini)                      |
|  - ai_service.py: Structured JSON output generation                     |
|  - navigation_engine.py: Care level & timeframe mapping                 |
|  - final_assessment.py: Non-diagnostic synthesis & safe normalization   |
+-------------------------------------------------------------------------+
```

## Key Architectural Invariants

1. **Deterministic Precedence**: Deterministic safety checks run strictly before any AI invocation and again upon receipt of each follow-up response.
2. **Authoritative Safety**: The LLM can interpret natural language, but deterministic red flags always have unilateral authority to interrupt the session into an Emergency state.
3. **No Phantom Citations**: Care level, recommended timeframe, and escalation criteria are strictly constrained to predefined clinical buckets.
4. **Client-Side Privacy**: Geolocation for the "Find Nearest Care" feature is one-shot via `navigator.geolocation` and executed entirely on the client side without storing coordinates or sending them to the backend.
