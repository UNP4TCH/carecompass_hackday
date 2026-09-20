# AI Workflow & Multimodal Reasoning

*Updated: September 20, 2026 — Hackday 1.0 Submission*

## 1. Initial Symptom Understanding
- **Input**: User's free-text symptom description.
- **Model**: `gemini-3.6-flash` with structured Pydantic schema validation.
- **Extraction Targets**:
  - Identified symptoms list
  - Timeline & duration
  - Severity level
  - Clinical & situational context
  - Missing information flags

## 2. Adaptive Question Selection
- Before generating a question, the conversation engine passes the cumulative case state.
- Gemini returns:
  - `should_continue = true` with exactly one targeted question addressing missing details, or
  - `should_continue = false` when sufficient data exists for cautious navigation.
- Duplicate questions and conversational loops are barred by the turn cap (default max 7 turns).

## 3. Answer Interpretation & Reassessment
- User replies are classified as direct answers, clarifications, or unrelated input.
- Any newly reported symptoms trigger an immediate pass through `triage_engine.py` to ensure emergent red flags have not emerged mid-conversation.

## 4. Final Guidance Generation
- Generates structured, cautious guidance:
  - Concise summary of reported symptoms
  - Recommended next steps & timeframe
  - Plain-language explanation ("Why")
  - Specific warning signs that require emergency escalation
  - Care setting assignment (Self-Care, Primary Care, Urgent Care, Emergency)
  - Medical disclaimers

## 5. Multimodal Document Simplification
- Accepts image uploads of doctor notes, prescription labels, and discharge instructions.
- Pillow validates image integrity before passing bytes to Gemini.
- Formats unstructured medical paperwork into standardized medication schedules, dosages, special precautions, and highlighted uncertain/unreadable entries.
