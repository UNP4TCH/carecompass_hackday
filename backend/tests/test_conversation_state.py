# CareCompass Test Suite — Updated: September 20, 2026 — Hackday 1.0
from services.conversation_engine import create_conversation


def test_answer_history_is_preserved():
    state = create_conversation(
        "I have a headache."
    )

    state.set_question(
        "How long have you had the headache?",
    )

    state.record_answer(
        "For three days."
    )

    state.set_question(
        "Has anything changed?",
    )

    state.record_answer(
        "Actually, it started this morning."
    )

    assert len(state.answers) == 2

    assert "For three days." in state.answers.values()
    assert "Actually, it started this morning." in state.answers.values()


def test_scalar_case_information_can_be_corrected():
    state = create_conversation(
        "I have a headache."
    )

    state.set_known_information(
        "duration",
        "three days",
    )

    state.set_known_information(
        "duration",
        "this morning",
    )

    assert state.known_information["duration"] == "this morning"


def test_list_information_is_deduplicated():
    state = create_conversation(
        "I have a headache."
    )

    state.append_known_information(
        "symptoms",
        ["headache", "nausea"],
    )

    state.append_known_information(
        "symptoms",
        ["nausea", "dizziness"],
    )

    assert state.known_information["symptoms"] == [
        "headache",
        "nausea",
        "dizziness",
    ]


def test_safety_flags_are_deduplicated():
    state = create_conversation(
        "I have symptoms."
    )

    state.add_safety_flags(
        ["stroke", "breathing"]
    )

    state.add_safety_flags(
        ["stroke", "seizure"]
    )

    assert state.safety_flags == [
        "stroke",
        "breathing",
        "seizure",
    ]


def test_completed_state_cannot_receive_question():
    state = create_conversation(
        "I have a headache."
    )

    state.complete()

    try:
        state.set_question(
            "How severe is it?"
        )
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass