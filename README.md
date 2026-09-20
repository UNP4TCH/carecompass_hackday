# CareCompass

**AI-powered first-step healthcare navigation — not diagnosis.**

*Hackday 1.0 Submission — Updated September 20, 2026*

CareCompass is a safety-first healthcare navigation platform that turns unstructured symptom descriptions or complex medical documents into clear, cautious next-step guidance and doctor-ready summaries.

---

## Core Architecture

```text
User Symptom Description OR Medical Document Photo
      ↓
Deterministic Safety Gate (Keyword & Pattern Triage)
      ↓
AI Multimodal Understanding (Gemini Flash)
      ↓
Adaptive Next Question OR Document Simplification
      ↓
User Answer / Review
      ↓
Safety Re-Check & Navigation Assignment
      ↓
Final Cautious Guidance + Doctor-Ready Care Summary (PDF / Print)
```

The **deterministic safety layer is independent of Gemini**. Gemini is used for language understanding, information extraction, adaptive question selection, and final non-diagnostic guidance. If emergency symptoms are detected, deterministic rules immediately interrupt the flow.

---

## Complete Feature Matrix

### Phase 1: Care Navigation Instrument
- **Adaptive Question Flow**: Asks targeted clarifying questions based on missing clinical context, bounded by turn caps.
- **Deterministic Red-Flag Safety Gate**: Independent pattern matcher intercepts severe symptoms before AI is invoked.
- **Continuous Reassessment**: Evaluates new symptoms mentioned in follow-up answers.
- **AI Fail-Safe State**: Gracefully degrades to safety guidance if upstream APIs or rate limits (HTTP 429) occur.

### Phase 2 & 2.1: Find Nearest Care
- **Browser Geolocation**: One-shot client-side geolocation query (no server-side tracking, no persistent storage).
- **Direct Maps Integration**: Launches direct Google Maps searches for Emergency Departments, Urgent Care, or Primary Care Clinics.
- **Emergency Integration**: 1-click nearby ER search directly accessible from the emergency interrupt screen.

### Phase 3: Prescription & Discharge Note Simplifier
- **Multimodal Document Analysis**: Gemini extracts instructions from prescription photos and discharge notes.
- **Structured Actionable Cards**: Plain-language tables with medication dosage, timing, purpose, and dietary rules.
- **Unclear / Illegible Flags**: Prominently highlights unreadable handwriting or dosages for pharmacist verification.
- **Patient Safety Disclaimer**: Explicitly reminds users to verify with their doctor or pharmacist.

### Phase 4: Download Care Summary
- **Doctor-Ready Clinical Summary**: Standardized, clean summary containing symptoms, timeline, answers, and urgency rating.
- **Native Browser Print**: Uses `window.print()` and custom `@media print` CSS for pixel-perfect PDF export without external dependencies.

### Phase 5: Testing & Quality Assurance
- **50 Automated Tests**: 100% passing across 10 unit, API, and safety test suites.
- **Production Build**: Zero-error Vite frontend build.

---

## Requirements

- Python 3.11+ recommended (Python 3.14 compatible)
- Node.js 20+ recommended
- Gemini API key for live AI features (`gemini-3.6-flash` default)

---

## 1. Backend Setup

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` with your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

Start the backend server:

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

---

## 2. Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 3. Automated Test Suite

From the `backend/` directory:

```bash
pytest -v
```

All 50 unit and integration tests run in ~3 seconds. AI question selectors and document mocks prevent unnecessary API quota consumption during testing.

---

## 4. Safety Principles & Limitations

CareCompass deliberately does **NOT**:
- Diagnose medical conditions or diseases
- Prescribe medication or adjust dosages
- Replace 911, emergency medical services, or professional consultation
- Guarantee medical accuracy without clinical review

---

## 5. Repository Structure

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
│   │   ├── document_service.py
│   │   ├── final_assessment.py
│   │   ├── navigation_engine.py
│   │   └── triage_engine.py
│   └── tests/
│       ├── test_adaptive_contract.py
│       ├── test_api.py
│       ├── test_assessment_safety.py
│       ├── test_conversation_engine.py
│       ├── test_conversation_state.py
│       ├── test_document_simplifier.py
│       ├── test_final_assessment.py
│       ├── test_navigation_engine.py
│       ├── test_triage_engine.py
│       └── test_triage_engine_v2.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── main.jsx
│       ├── components/
│       │   ├── AssessmentView.jsx
│       │   ├── CareSummaryDocument.jsx
│       │   ├── Chrome.jsx
│       │   ├── DocumentSimplifierView.jsx
│       │   ├── EmergencyView.jsx
│       │   ├── FindNearestCare.jsx
│       │   ├── IntakeView.jsx
│       │   ├── ResultView.jsx
│       │   ├── UnavailableView.jsx
│       │   └── icons.jsx
│       └── lib/
│           ├── nearestCare.js
│           ├── presentation.js
│           └── useFocusOnMount.js
├── docs/
│   ├── architecture.md
│   ├── ai-workflow.md
│   └── demo-script.md
├── scripts/
│   ├── setup_windows.ps1
│   └── setup_unix.sh
└── README.md
```
