"""Gemini-backed reasoning layer for CareCompass.

The LLM is used for language understanding and question selection. It does not
make the application's emergency decision; that responsibility stays in the
deterministic safety layer.

This module also provides bounded retry handling for transient Gemini failures.
"""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

client = genai.Client(api_key=API_KEY) if API_KEY else None


# ---------------------------------------------------------------------------
# RETRY CONFIGURATION
# ---------------------------------------------------------------------------

MAX_RETRIES = 2

# Short delays keep the application responsive while allowing temporary
# Gemini 503/service-unavailable errors a chance to recover.
RETRY_DELAYS = (2, 5)


# ---------------------------------------------------------------------------
# AI RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class SymptomAnalysis(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    duration: str = ""
    severity: str = ""
    context: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class CaseUpdates(BaseModel):
    """Structured updates to the current case state."""

    symptoms: list[str] = Field(default_factory=list)
    duration: str = ""
    severity: str = ""
    context: list[str] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    answers_current_question: bool = False
    extracted_answer: str = ""

    new_symptoms: list[str] = Field(default_factory=list)

    extracted_facts: list[str] = Field(default_factory=list)

    case_updates: CaseUpdates = Field(
        default_factory=CaseUpdates
    )

    response_type: str = "unrelated"
    suggested_response: str = ""


class NextQuestion(BaseModel):
    should_continue: bool = True
    question: str = ""
    rationale: str = ""
    information_target: str = ""


class FinalAssessment(BaseModel):
    summary: str = ""
    urgency: str = "routine_follow_up"
    recommended_action: str = ""
    why: str = ""
    warning_signs: list[str] = Field(default_factory=list)
    care_level: str = "routine"
    disclaimer: str = (
        "CareCompass provides preliminary navigation guidance and does not "
        "provide a medical diagnosis or replace a qualified clinician."
    )


# ---------------------------------------------------------------------------
# CLIENT
# ---------------------------------------------------------------------------

def is_configured() -> bool:
    return client is not None


def _require_client() -> genai.Client:
    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return client


# ---------------------------------------------------------------------------
# ERROR CLASSIFICATION
# ---------------------------------------------------------------------------

def _is_retryable_error(exc: Exception) -> bool:
    """Return True for temporary Gemini failures worth retrying."""

    status_code = getattr(exc, "code", None)

    if status_code in {500, 502, 503, 504}:
        return True

    message = str(exc).upper()

    temporary_markers = (
        "503 UNAVAILABLE",
        "SERVICE UNAVAILABLE",
        "TEMPORARILY UNAVAILABLE",
        "INTERNAL SERVER ERROR",
        "BAD GATEWAY",
        "GATEWAY TIMEOUT",
    )

    return any(
        marker in message
        for marker in temporary_markers
    )


def _is_quota_error(exc: Exception) -> bool:
    """Return True when Gemini reports exhausted quota/rate limits."""

    status_code = getattr(exc, "code", None)

    if status_code == 429:
        return True

    message = str(exc).upper()

    return (
        "RESOURCE_EXHAUSTED" in message
        or "QUOTA EXCEEDED" in message
        or "RATE LIMIT" in message
    )


# ---------------------------------------------------------------------------
# GEMINI REQUEST
# ---------------------------------------------------------------------------

def _generate(
    prompt: str,
    schema: type[BaseModel],
) -> dict:
    """Generate structured JSON from Gemini with bounded retry handling."""

    service = _require_client()

    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):

        try:
            response = service.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.2,
                ),
            )

            return schema.model_validate_json(
                response.text
            ).model_dump()

        except Exception as exc:
            last_error = exc

            # Quota errors should NOT be hammered repeatedly.
            #
            # If the free-tier daily quota is exhausted, retrying immediately
            # only wastes time and another request. Let the upper layer handle
            # the failure safely.
            if _is_quota_error(exc):
                raise

            # Temporary service failures can recover after a short delay.
            if _is_retryable_error(exc) and attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAYS[attempt])
                continue

            raise

    # Defensive fallback; normally unreachable because every failed attempt
    # either retries or raises.
    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "Gemini request failed without returning an exception."
    )


# ---------------------------------------------------------------------------
# INITIAL SYMPTOM UNDERSTANDING
# ---------------------------------------------------------------------------

def analyze_symptoms(
    user_text: str,
) -> dict:

    prompt = f"""
You are the language-understanding component of CareCompass.

Do not diagnose.
Do not give treatment instructions.

Extract only information explicitly supported by the user's words.

Identify:
- symptoms
- duration
- severity
- relevant context
- important missing information

Important:
Do not infer facts that the user did not state.

USER:
{user_text}
"""

    return _generate(
        prompt,
        SymptomAnalysis,
    )


# ---------------------------------------------------------------------------
# CONVERSATION RESPONSE UNDERSTANDING
# ---------------------------------------------------------------------------

def understand_conversation_response(
    current_question: str,
    user_answer: str,
) -> dict:

    prompt = f"""
You are the conversation-understanding component of CareCompass.

You are NOT diagnosing the user.

CURRENT QUESTION:
{current_question}

USER RESPONSE:
{user_answer}

Determine whether the response answers the current question.

Classify response_type as exactly one of:
- answer
- clarification
- unrelated

Extract:
1. A concise answer to the current question.
2. Any genuinely new symptoms explicitly mentioned.
3. Any additional facts explicitly stated.
4. Any structured updates to the user's current case understanding.

For case_updates:

- Only populate a field when the user explicitly provides information
  relevant to that field.
- If the user corrects previous information, return the NEW value.
- Do not preserve an old value when the user explicitly corrects it.
- Do not infer values that were not stated.
- An empty string means "no update".

Examples:

User:
"I've had it for three days."

case_updates:
{{
    "duration": "three days"
}}

Later user:
"Actually, it started this morning."

case_updates:
{{
    "duration": "this morning"
}}

The second value is a correction and should replace the earlier duration.

Another example:

User:
"It was mild, but now it's severe."

case_updates:
{{
    "severity": "severe"
}}

Do not diagnose.
Do not invent facts.
Do not provide medical advice.
"""

    return _generate(
        prompt,
        ConversationResponse,
    )


# ---------------------------------------------------------------------------
# ADAPTIVE QUESTION GENERATION
# ---------------------------------------------------------------------------

def generate_next_question(
    *,
    original_symptoms: str,
    known_information: dict[str, Any],
    answers: dict[str, str],
    questions_asked: list[str],
) -> dict:
    """Select one adaptive next question, or stop if enough information exists."""

    prompt = f"""
You are the adaptive questioning component of CareCompass.

You are NOT diagnosing the user and must not provide treatment instructions.

Goal:
Decide whether one more question is necessary to produce cautious,
non-diagnostic next-step guidance.

If a question is needed:
- ask exactly ONE high-value question
- fill the most important remaining information gap
- do not repeat previous questions
- prefer severity, onset, duration, progression, associated symptoms,
  or relevant context when appropriate
- avoid irrelevant personal information

IMPORTANT:
The KNOWN INFORMATION represents the CURRENT understanding of the case.
Use it instead of assuming older answers are still correct when they conflict.

ORIGINAL SYMPTOMS:
{original_symptoms}

CURRENT KNOWN INFORMATION:
{known_information}

ANSWERS SO FAR:
{answers}

QUESTIONS ALREADY ASKED:
{questions_asked}

Stop when enough information has been gathered for a cautious navigation
recommendation.

Never diagnose.
Never override the deterministic safety layer.
"""

    return _generate(
        prompt,
        NextQuestion,
    )


# ---------------------------------------------------------------------------
# FINAL ASSESSMENT
# ---------------------------------------------------------------------------

def generate_final_assessment(
    *,
    symptoms: str,
    known_information: dict[str, Any],
    answers: dict[str, str],
    safety_flags: list[str],
) -> dict:

    prompt = f"""
You are the final guidance component of CareCompass.

CareCompass is a preliminary healthcare navigation tool, not a diagnostic
system.

Produce cautious next-step guidance from the information supplied.

Never diagnose.
Never prescribe medication or dosages.
Never claim certainty.
Never override an emergency decision made by the deterministic safety layer.

If safety_flags is non-empty, use the safest appropriate urgency.

IMPORTANT:
KNOWN INFORMATION represents the latest structured understanding of the case.
When it conflicts with older ANSWERS, prefer the latest structured
KNOWN INFORMATION.

ORIGINAL SYMPTOMS:
{symptoms}

CURRENT KNOWN INFORMATION:
{known_information}

CONVERSATION ANSWERS:
{answers}

SAFETY FLAGS:
{safety_flags}

Choose urgency exactly from:
- emergency
- prompt_medical_attention
- routine_follow_up
- self_care_monitoring

Choose care_level exactly from:
- emergency
- urgent
- routine
- self_care

The recommended_action should tell the user what level of care to consider,
without pretending to make a diagnosis.

Warning signs should be concrete and safety-oriented.
"""

    return _generate(
        prompt,
        FinalAssessment,
    )


# ---------------------------------------------------------------------------
# BACKWARD COMPATIBILITY
# ---------------------------------------------------------------------------

def generate_final_assessment_legacy(
    *,
    symptoms: str,
    known_information: dict[str, Any],
    answers: dict[str, str],
    safety_flags: list[str],
) -> dict:
    """Backward-compatible alias for older callers."""

    return generate_final_assessment(
        symptoms=symptoms,
        known_information=known_information,
        answers=answers,
        safety_flags=safety_flags,
    )