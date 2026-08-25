import pytest

from services.assessment_engine import start_assessment, process_answer
from services.conversation_engine import create_conversation


# ---------------------------------------------------------------------------
# START-OF-ASSESSMENT SAFETY
# ---------------------------------------------------------------------------

def test_emergency_is_caught_before_ai():
    state, result = start_assessment(
        "I am struggling to breathe and cannot catch my breath."
    )

    assert result["status"] == "emergency"
    assert result["stage"] == "safety_check"
    assert state.completed is True
    assert result["next_question"] is None
    assert result["final_assessment"] is None


# ---------------------------------------------------------------------------
# NORMAL INPUT DOES NOT AUTOMATICALLY ESCALATE
# ---------------------------------------------------------------------------

def test_normal_input_passes_safety_gate(monkeypatch):
    def fake_analyze(symptoms):
        return {
            "symptoms": ["mild headache"],
            "duration": "today",
            "severity": "mild",
            "context": [],
            "missing_information": ["severity"],
        }

    def fake_question(**kwargs):
        return {
            "should_continue": True,
            "question": "How severe is the headache?",
            "rationale": "Need severity.",
        }

    monkeypatch.setattr(
        "services.assessment_engine.analyze_symptoms",
        fake_analyze,
    )

    monkeypatch.setattr(
        "services.assessment_engine.generate_next_question",
        fake_question,
    )

    state, result = start_assessment(
        "I have a mild headache since this morning."
    )

    assert result["status"] == "assessment_started"
    assert state.completed is False
    assert result["next_question"] is not None


# ---------------------------------------------------------------------------
# EMERGENCY INTRODUCED DURING ANSWER
# ---------------------------------------------------------------------------

def test_emergency_answer_stops_assessment():
    state = create_conversation(
        "I have a mild headache since this morning."
    )

    state.set_question(
        "How severe is your headache?",
        "Need severity.",
    )

    state, result = process_answer(
        state,
        "Actually, I am suddenly having trouble speaking.",
    )

    assert result["status"] == "emergency"
    assert result["stage"] == "answer_safety_check"
    assert state.completed is True
    assert result["next_question"] is None
    assert result["final_assessment"] is None


# ---------------------------------------------------------------------------
# CUMULATIVE SAFETY
# ---------------------------------------------------------------------------

def test_cumulative_case_is_checked(monkeypatch):
    def fake_understand(question, answer):
        return {
            "response_type": "answer",
            "answers_current_question": True,
            "extracted_answer": answer,
            "new_symptoms": [],
            "extracted_facts": [],
        }

    def fake_question(**kwargs):
        return {
            "should_continue": True,
            "question": "Any other symptoms?",
            "rationale": "Continue assessment.",
        }

    monkeypatch.setattr(
        "services.assessment_engine.understand_conversation_response",
        fake_understand,
    )

    monkeypatch.setattr(
        "services.assessment_engine.generate_next_question",
        fake_question,
    )

    state = create_conversation(
        "I have chest pain."
    )

    state.set_question(
        "How severe is the pain?",
        "Need severity.",
    )

    state, result = process_answer(
        state,
        "It is mild.",
    )

    # The original case contains "chest pain", so the cumulative
    # safety check should still see it.
    assert result["status"] == "emergency"
    assert state.completed is True


# ---------------------------------------------------------------------------
# AI FAILURE MUST NOT CREATE AN ASSESSMENT
# ---------------------------------------------------------------------------

def test_ai_failure_returns_safe_unavailable_state(monkeypatch):
    def failing_ai(symptoms):
        raise RuntimeError("AI unavailable")

    monkeypatch.setattr(
        "services.assessment_engine.analyze_symptoms",
        failing_ai,
    )

    state, result = start_assessment(
        "I have a mild headache since this morning."
    )

    assert result["status"] == "ai_unavailable"
    assert result["final_assessment"] is None
    assert result["next_question"] is None