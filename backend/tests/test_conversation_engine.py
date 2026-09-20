# CareCompass Test Suite — Updated: September 20, 2026 — Hackday 1.0
from services.conversation_engine import create_conversation


def test_state_records_question_and_answer():
    state = create_conversation("I have a headache")
    question = state.set_question("How long have you had it?")
    assert question["question_id"] == "q_1"
    state.record_answer("Since yesterday")
    assert state.answers["q_1"] == "Since yesterday"
    assert state.turn_count == 1
    assert state.current_question is None
