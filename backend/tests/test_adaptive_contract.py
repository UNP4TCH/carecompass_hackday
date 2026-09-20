"""Contract-level tests for the adaptive engine without calling Gemini.
Updated: September 20, 2026 — Hackday 1.0
"""
from services.assessment_engine import _ask_next_question
from services.conversation_engine import create_conversation
import services.assessment_engine as engine


def test_question_changes_after_state_changes(monkeypatch):
    state = create_conversation("headache for two days")
    calls = []

    def fake_next_question(**kwargs):
        calls.append(kwargs)
        if not kwargs["answers"]:
            return {"should_continue": True, "question": "How severe is the headache?", "rationale": "severity", "information_target": "severity"}
        return {"should_continue": True, "question": "Did it begin suddenly or gradually?", "rationale": "onset", "information_target": "onset"}

    monkeypatch.setattr(engine, "generate_next_question", fake_next_question)
    first = _ask_next_question(state)
    assert first["question"] == "How severe is the headache?"
    state.record_answer("moderate")
    second = _ask_next_question(state)
    assert second["question"] == "Did it begin suddenly or gradually?"
    assert len(calls) == 2
