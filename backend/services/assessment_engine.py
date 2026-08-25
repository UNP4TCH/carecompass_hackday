"""Core CareCompass assessment orchestration.

The assessment engine coordinates:
    - deterministic safety screening
    - AI-assisted symptom understanding
    - adaptive questioning
    - conversation state
    - final assessment generation

The deterministic safety layer always has authority over emergency escalation.
"""

from __future__ import annotations

from services.ai_service import (
    analyze_symptoms,
    generate_next_question,
    understand_conversation_response,
)
from services.conversation_engine import ConversationState, create_conversation
from services.final_assessment import build_final_assessment
from services.triage_engine import check_emergency_signs


# ---------------------------------------------------------------------------
# AI FAILURE HANDLING
# ---------------------------------------------------------------------------


def _ai_unavailable(
    state: ConversationState,
    stage: str,
    exc: Exception,
) -> dict:
    """Return a safe response when an AI service call fails."""

    cumulative_triage = _check_cumulative_safety(state)

    return {
        "status": "ai_unavailable",
        "stage": stage,
        "triage": cumulative_triage,
        "next_question": None,
        "final_assessment": None,
        "message": (
            "CareCompass AI is temporarily unavailable. "
            "Check your API key/model configuration and try again."
        ),
        "error_code": getattr(exc, "code", None),
    }

# ---------------------------------------------------------------------------
# SAFETY ORCHESTRATION
# ---------------------------------------------------------------------------


def _build_safety_context(state: ConversationState) -> str:
    """Build a deterministic text representation of the current case.

    This is intentionally simple. The safety engine remains deterministic
    and independent of the LLM.
    """
    parts: list[str] = []

    if state.original_symptoms:
        parts.append(state.original_symptoms)

    for answer in state.answers:
        if isinstance(answer, dict):
            answer_text = (
                answer.get("answer")
                or answer.get("extracted_answer")
                or answer.get("text")
                or ""
            )
        else:
            answer_text = str(answer)

        if answer_text.strip():
            parts.append(answer_text.strip())

    known_information = state.known_information or {}

    for key in ("symptoms", "new_symptoms", "context", "facts"):
        values = known_information.get(key, [])

        if isinstance(values, str):
            values = [values]

        if isinstance(values, list):
            for value in values:
                if value:
                    parts.append(str(value))

    return " ".join(parts)


def _check_cumulative_safety(state: ConversationState) -> dict:
    """Run the deterministic safety gate against the complete case."""
    context = _build_safety_context(state)

    return check_emergency_signs(context)


def _register_emergency(
    state: ConversationState,
    triage: dict,
) -> None:
    """Record safety flags and terminate the assessment."""
    for sign in triage.get("detected_signs", []):
        if sign not in state.safety_flags:
            state.safety_flags.append(sign)

    state.complete()


def _emergency_response(
    state: ConversationState,
    triage: dict,
    stage: str,
) -> dict:
    """Create the standard emergency response."""
    _register_emergency(state, triage)

    return {
        "status": "emergency",
        "stage": stage,
        "triage": triage,
        "next_question": None,
        "final_assessment": None,
    }


# ---------------------------------------------------------------------------
# QUESTION GENERATION
# ---------------------------------------------------------------------------


def _ask_next_question(
    state: ConversationState,
) -> dict | None:
    if state.turn_count >= state.max_turns:
        return None

    result = generate_next_question(
        original_symptoms=state.original_symptoms,
        known_information=state.known_information,
        answers=state.answers,
        questions_asked=state.asked_questions(),
    )

    if not result.get("should_continue"):
        return None

    question = (result.get("question") or "").strip()

    if not question:
        return None

    asked = {q.lower() for q in state.asked_questions()}

    if question.lower() in asked:
        return None

    return state.set_question(
        question,
        result.get("rationale", ""),
    )


# ---------------------------------------------------------------------------
# FINAL ASSESSMENT
# ---------------------------------------------------------------------------


def _finish(
    state: ConversationState,
    triage: dict,
) -> tuple[ConversationState, dict]:
    # Run one final deterministic safety check immediately before
    # allowing the assessment to complete.
    final_triage = _check_cumulative_safety(state)

    if final_triage["level"] == "emergency":
        return state, _emergency_response(
            state,
            final_triage,
            "final_safety_check",
        )

    final = build_final_assessment(
        symptoms=state.original_symptoms,
        known_information=state.known_information,
        answers=state.answers,
        safety_flags=state.safety_flags,
    )

    # Deterministic safety always has final authority.
    if state.safety_flags or final_triage.get("level") == "emergency":
        final["urgency"] = "emergency"
        final["care_level"] = "emergency"
        final["recommended_action"] = (
            "Seek immediate professional medical attention or "
            "contact your local emergency service."
        )

    state.complete()

    return state, {
        "status": "assessment_complete",
        "stage": "assessment_complete",
        "triage": final_triage,
        "next_question": None,
        "answers": state.answers,
        "final_assessment": final,
    }


# ---------------------------------------------------------------------------
# START ASSESSMENT
# ---------------------------------------------------------------------------


def start_assessment(
    symptoms: str,
) -> tuple[ConversationState, dict]:
    symptoms = (symptoms or "").strip()
    state = create_conversation(symptoms)

    if len(symptoms) < 3:
        return state, {
            "status": "validation_error",
            "stage": "input_validation",
            "message": (
                "Please describe what you are experiencing "
                "in a little more detail."
            ),
            "next_question": None,
        }

    # ---------------------------------------------------------------
    # FIRST SAFETY GATE
    # ---------------------------------------------------------------

    triage = check_emergency_signs(symptoms)

    if triage["level"] == "emergency":
        return state, _emergency_response(
            state,
            triage,
            "safety_check",
        )

    # ---------------------------------------------------------------
    # AI INITIAL ANALYSIS
    # ---------------------------------------------------------------

    try:
        analysis = analyze_symptoms(symptoms)

        state.known_information = {
            "symptoms": analysis.get("symptoms", []),
            "duration": analysis.get("duration", ""),
            "severity": analysis.get("severity", ""),
            "context": analysis.get("context", []),
            "missing_information": analysis.get(
                "missing_information",
                [],
            ),
        }

        # -----------------------------------------------------------
        # SAFETY RECHECK AFTER AI EXTRACTION
        # -----------------------------------------------------------

        triage = _check_cumulative_safety(state)

        if triage["level"] == "emergency":
            return state, _emergency_response(
                state,
                triage,
                "post_analysis_safety_check",
            )

        question = _ask_next_question(state)

    except Exception as exc:
        return state, _ai_unavailable(
            state,
            "ai_service",
            exc,
        )

    if question is None:
        try:
            return _finish(state, triage)
        except Exception as exc:
            return state, _ai_unavailable(
                state,
                "final_assessment_ai",
                exc,
            )

    return state, {
        "status": "assessment_started",
        "stage": "information_gathering",
        "triage": triage,
        "ai_analysis": state.known_information,
        "next_question": question,
        "answers": state.answers,
    }


# ---------------------------------------------------------------------------
# PROCESS ANSWER
# ---------------------------------------------------------------------------


def process_answer(
    state: ConversationState,
    answer: str,
) -> tuple[ConversationState, dict]:
    answer = (answer or "").strip()

    if state.completed:
        return state, {
            "status": "error",
            "message": "This assessment is already complete.",
        }

    if not answer:
        return state, {
            "status": "validation_error",
            "message": "Please provide an answer.",
        }

    if not state.current_question:
        return state, {
            "status": "error",
            "message": "There is no active question.",
        }

    # ---------------------------------------------------------------
    # SAFETY CHECK #1
    # Raw user answer
    # ---------------------------------------------------------------

    raw_safety = check_emergency_signs(answer)

    if raw_safety["level"] == "emergency":
        return state, _emergency_response(
            state,
            raw_safety,
            "answer_safety_check",
        )

    current_question = state.current_question["question"]

    # ---------------------------------------------------------------
    # AI INTERPRETATION
    # ---------------------------------------------------------------

    try:
        response = understand_conversation_response(
            current_question,
            answer,
        )

    except Exception as exc:
        return state, _ai_unavailable(
            state,
            "conversation_ai",
            exc,
        )

    # ---------------------------------------------------------------
    # NEW SYMPTOM SAFETY CHECK
    # ---------------------------------------------------------------

    new_symptoms = response.get("new_symptoms", [])

    if new_symptoms:
        new_symptom_text = " ".join(
            str(symptom)
            for symptom in new_symptoms
            if symptom
        )

        new_safety = check_emergency_signs(
            new_symptom_text
        )

        if new_safety["level"] == "emergency":
            return state, _emergency_response(
                state,
                new_safety,
                "new_symptom_safety_check",
            )

    # ---------------------------------------------------------------
    # RESPONSE TYPE / CLARIFICATION
    # ---------------------------------------------------------------

    if (
        response.get("response_type") != "answer"
        or not response.get("answers_current_question")
    ):
        message = response.get(
            "suggested_response"
        ) or (
            "Please answer the current question so "
            "CareCompass can continue."
        )

        return state, {
            "status": "question_clarification",
            "stage": "information_gathering",
            "triage": raw_safety,
            "next_question": state.current_question,
            "assistant_message": message,
            "answers": state.answers,
        }

    # ---------------------------------------------------------------
    # RECORD ANSWER
    # ---------------------------------------------------------------

    extracted = (
        response.get("extracted_answer")
        or answer
    ).strip()

    state.record_answer(extracted)

    # ---------------------------------------------------------------
    # APPLY STRUCTURED CASE UPDATES
    # ---------------------------------------------------------------

    case_updates = response.get("case_updates") or {}

    if case_updates:
        scalar_updates = {}

        for key in ("duration", "severity"):
            value = (case_updates.get(key) or "").strip()

            if value:
                scalar_updates[key] = value

        if scalar_updates:
            state.update_known_information(
                scalar_updates
            )

        for key in ("symptoms", "context"):
            values = case_updates.get(key) or []

            if values:
                state.append_known_information(
                    key,
                    values,
                )

    # ---------------------------------------------------------------
    # PRESERVE NEWLY DISCOVERED SYMPTOMS
    # ---------------------------------------------------------------

    if new_symptoms:
        state.append_known_information(
            "new_symptoms",
            new_symptoms,
        )

    # ---------------------------------------------------------------
    # PRESERVE EXPLICITLY EXTRACTED FACTS
    # ---------------------------------------------------------------

    extracted_facts = response.get(
        "extracted_facts",
        [],
    )

    if extracted_facts:
        state.append_known_information(
            "facts",
            extracted_facts,
        )

    # ---------------------------------------------------------------
    # CUMULATIVE SAFETY RECHECK
    #
    # We don't only check the latest answer.
    # We check the complete evolving case.
    # ---------------------------------------------------------------

    cumulative_safety = _check_cumulative_safety(state)

    if cumulative_safety["level"] == "emergency":
        return state, _emergency_response(
            state,
            cumulative_safety,
            "cumulative_safety_check",
        )

    # ---------------------------------------------------------------
    # NEXT QUESTION / FINAL ASSESSMENT
    # ---------------------------------------------------------------

    try:
        question = _ask_next_question(state)

        if question is None:
            return _finish(
                state,
                cumulative_safety,
            )

    except Exception as exc:
        return state, _ai_unavailable(
            state,
            "adaptive_question_ai",
            exc,
        )

    return state, {
        "status": "answer_recorded",
        "stage": "information_gathering",
        "triage": cumulative_safety,
        "next_question": question,
        "answers": state.answers,
    }
