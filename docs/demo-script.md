# CareCompass 3-Minute Demo Runbook

*Updated: September 20, 2026 — Hackday 1.0 Submission*

---

### Step 1: Emergency Triage Interception (Safety-First)
1. In the Triage Assessment view, enter:
   > *"I have crushing chest pain that radiates to my left arm, and I am feeling short of breath."*
2. Click **"Begin Assessment"**.
3. **Key talking points**:
   - Immediate transition to the Emergency screen with clear safety instructions.
   - Deterministic rule screening prevents LLM latency in acute emergencies.
   - Highlights the 1-click **"Find Nearest Emergency Department"** button linking to nearby hospitals via Google Maps.
4. Click **"Start Over"**.

---

### Step 2: Adaptive Questioning & Download Care Summary
1. Enter a non-emergency symptom:
   > *"I have had a mild tension headache for the past 2 hours after staring at my monitor all morning."*
2. Click **"Begin Assessment"**.
3. Answer the dynamic follow-up question (e.g., *"No vision changes or nausea, just dull forehead pressure"*).
4. Review the result view:
   - Care Level: Self-Care / Routine.
   - Recommended timeframe: 24–48 hours or home rest.
   - **Find Nearest Care**: Point out nearby clinic search options.
   - Click **"Download Care Summary"**: Shows the clean, doctor-ready print layout (PDF export).

---

### Step 3: Prescription & Discharge Note Simplifier
1. Click the **"Simplify Document"** tab in the navigation bar.
2. Upload a sample prescription or doctor's note image (JPEG, PNG, or WEBP).
3. **Key talking points**:
   - Multimodal Gemini extraction structures complex handwriting and medical jargon into plain language.
   - Uncertain or illegible items are explicitly highlighted for pharmacist confirmation.
   - Emphasizes patient safety disclaimers.
