"""Deterministic care-navigation layer for CareCompass.

This module converts an already-generated CareCompass urgency/care-level
assessment into structured navigation guidance.

It does not diagnose conditions and does not determine emergency status.
Emergency authority remains with the deterministic safety engine.
"""

from __future__ import annotations

from typing import Any


NAVIGATION_MAP: dict[str, dict[str, Any]] = {
    "emergency": {
        "label": "Immediate attention",
        "timeframe": "Now",
        "setting": "Emergency medical care",
        "action": (
            "Seek immediate professional medical attention or "
            "contact your local emergency service."
        ),
        "escalation": (
            "Do not wait for symptoms to improve before seeking "
            "emergency help."
        ),
    },
    "urgent": {
        "label": "Prompt medical attention",
        "timeframe": "Today / as soon as reasonably possible",
        "setting": "Urgent medical evaluation",
        "action": (
            "Consider seeking prompt in-person medical evaluation "
            "from an appropriate healthcare professional."
        ),
        "escalation": (
            "If symptoms become severe, suddenly worsen, or new "
            "emergency warning signs appear, seek emergency care."
        ),
    },
    "routine": {
        "label": "Routine care",
        "timeframe": "Schedule when practical",
        "setting": "Primary care or appropriate healthcare professional",
        "action": (
            "Consider scheduling a healthcare appointment if the "
            "symptoms persist, recur, or continue affecting daily life."
        ),
        "escalation": (
            "Seek more urgent care if symptoms worsen or new "
            "warning signs appear."
        ),
    },
    "self_care": {
        "label": "Self-care & monitoring",
        "timeframe": "Monitor over the next few days",
        "setting": "Self-care with monitoring",
        "action": (
            "Monitor your symptoms and consider appropriate "
            "self-care measures. Seek professional advice if "
            "symptoms persist or worsen."
        ),
        "escalation": (
            "Seek medical attention if symptoms worsen, persist "
            "unexpectedly, or new warning signs develop."
        ),
    },
}


def build_care_navigation(
    *,
    urgency: str,
    care_level: str,
    safety_flags: list[str] | None = None,
) -> dict[str, Any]:
    """Build structured navigation guidance.

    Safety flags always force emergency navigation.
    """

    safety_flags = safety_flags or []

    # Deterministic safety authority.
    if safety_flags:
        urgency = "emergency"
        care_level = "emergency"

    # Prefer care_level when it maps directly to navigation.
    navigation_key = care_level

    if navigation_key not in NAVIGATION_MAP:
        navigation_key = {
            "prompt_medical_attention": "urgent",
            "routine_follow_up": "routine",
            "self_care_monitoring": "self_care",
        }.get(urgency, "routine")

    navigation = NAVIGATION_MAP[navigation_key]

    return {
        "level": navigation_key,
        "label": navigation["label"],
        "timeframe": navigation["timeframe"],
        "setting": navigation["setting"],
        "action": navigation["action"],
        "escalation": navigation["escalation"],
    }