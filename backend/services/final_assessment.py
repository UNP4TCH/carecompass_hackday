"""Final guidance orchestration.

This module is the final application-level guardrail around the AI-generated
assessment.

The LLM provides structured preliminary guidance, while deterministic safety
flags always have authority over emergency escalation.

Updated: September 20, 2026 — Hackday 1.0
"""

from __future__ import annotations

from typing import Any

from services.ai_service import generate_final_assessment
from services.navigation_engine import build_care_navigation


VALID_URGENCY = {
    "emergency",
    "prompt_medical_attention",
    "routine_follow_up",
    "self_care_monitoring",
}

VALID_CARE_LEVELS = {
    "emergency",
    "urgent",
    "routine",
    "self_care",
}


EMERGENCY_ACTION = (
    "Seek immediate professional medical attention or "
    "contact your local emergency service."
)


def _normalize_ai_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """Ensure the AI response has the expected structure."""

    result = result or {}

    urgency = result.get("urgency")

    if urgency not in VALID_URGENCY:
        urgency = "routine_follow_up"

    care_level = result.get("care_level")

    if care_level not in VALID_CARE_LEVELS:
        care_level = "routine"

    warning_signs = result.get("warning_signs")

    if not isinstance(warning_signs, list):
        warning_signs = []

    return {
        "summary": str(
            result.get("summary") or ""
        ).strip(),

        "urgency": urgency,

        "recommended_action": str(
            result.get("recommended_action") or ""
        ).strip(),

        "why": str(
            result.get("why") or ""
        ).strip(),

        "warning_signs": warning_signs,

        "care_level": care_level,

        "disclaimer": str(
            result.get("disclaimer")
            or (
                "CareCompass provides preliminary navigation guidance "
                "and does not provide a medical diagnosis or replace "
                "a qualified clinician."
            )
        ).strip(),
    }


def _apply_safety_authority(
    result: dict[str, Any],
    safety_flags: list[str],
) -> dict[str, Any]:
    """Apply deterministic safety authority over AI output."""

    if not safety_flags:
        return result

    result["urgency"] = "emergency"
    result["care_level"] = "emergency"
    result["recommended_action"] = EMERGENCY_ACTION

    return result


def build_final_assessment(
    *,
    symptoms: str,
    known_information: dict,
    answers: dict,
    safety_flags: list[str],
) -> dict:

    result = generate_final_assessment(
        symptoms=symptoms,
        known_information=known_information,
        answers=answers,
        safety_flags=safety_flags,
    )

    result = _normalize_ai_result(result)

    result = _apply_safety_authority(
        result,
        safety_flags,
    )

    result["navigation"] = build_care_navigation(
        urgency=result["urgency"],
        care_level=result["care_level"],
        safety_flags=safety_flags,
    )

    return result