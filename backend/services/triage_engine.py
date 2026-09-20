"""Deterministic safety gate for CareCompass.

Safety Engine v2

This module is deliberately independent of the LLM. It performs a conservative
first-pass screen for phrases that may indicate an emergency.

It does NOT diagnose conditions. Its responsibility is to identify potential
emergency warning signs and interrupt the normal AI assessment flow.

Updated: September 20, 2026 — Hackday 1.0
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# EMERGENCY PATTERNS
# ---------------------------------------------------------------------------

EMERGENCY_GROUPS: dict[str, tuple[str, ...]] = {
    "breathing": (
        "can't breathe",
        "cannot breathe",
        "difficulty breathing",
        "struggling to breathe",
        "gasping for air",
        "gasping",
        "choking",
        "not able to breathe",
        "unable to breathe",
        "can't catch my breath",
        "cannot catch my breath",
        "shortness of breath",
        "severe shortness of breath",
    ),

    "severe_chest_symptoms": (
        "severe chest pain",
        "crushing chest pain",
        "chest pain",
        "chest pressure",
        "pressure in my chest",
        "chest tightness",
        "tight chest",
        "chest feels tight",
        "chest feels heavy",
        "heavy chest",
        "severe pain in my chest",
    ),

    "heart_attack": (
        "heart attack",
        "having a heart attack",
        "possible heart attack",
        "heart attack symptoms",
    ),

    "stroke": (
        "face drooping",
        "one side of my face is drooping",
        "one side of my face",
        "arm weakness",
        "one arm is weak",
        "one side is weak",
        "can't lift my arm",
        "cannot lift my arm",
        "difficulty speaking",
        "speech is slurred",
        "my speech is slurred",
        "my speech is suddenly slurred",
        "speech suddenly became slurred",
        "my speech suddenly became slurred",
        "slurred speech",
        "can't speak",
        "cannot speak",
        "sudden confusion",
        "suddenly confused",
        "trouble speaking",
        "trouble talking",
        "difficulty talking",
    ),

    "consciousness": (
        "unconscious",
        "passed out",
        "fainted",
        "not responding",
        "cannot wake up",
        "can't wake up",
        "lost consciousness",
        "loss of consciousness",
    ),

    "severe_bleeding": (
        "severe bleeding",
        "heavy bleeding",
        "bleeding heavily",
        "blood won't stop",
        "bleeding won't stop",
        "bleeding that won't stop",
    ),

    "seizure": (
        "having a seizure",
        "having seizures",
        "seizure",
        "convulsions",
        "convulsion",
        "fitting",
        "fits",
    ),

    "coughing_blood": (
        "coughing blood",
        "coughing up blood",
        "blood in my cough",
        "bloody cough",
    ),

    "severe_allergic_reaction": (
        "throat is closing",
        "throat closing",
        "throat feels closed",
        "tongue swelling",
        "swelling of my tongue",
        "tongue is swollen",
        "severe allergic reaction",
        "anaphylaxis",
    ),

    "poisoning_overdose": (
        "overdose",
        "overdosed",
        "poisoned",
        "poisoning",
        "took too much",
        "swallowed poison",
        "ingested poison",
    ),
}


# ---------------------------------------------------------------------------
# CONTEXT
# ---------------------------------------------------------------------------

NEGATION_TERMS = {
    "no",
    "not",
    "never",
    "without",
    "none",
    "don't",
    "dont",
    "doesn't",
    "doesnt",
    "isn't",
    "isnt",
    "aren't",
    "arent",
    "haven't",
    "havent",
    "hasn't",
    "hasnt",
    "didn't",
    "didnt",
    "wasn't",
    "wasnt",
    "weren't",
    "werent",
    "neither",
}


HISTORICAL_MARKERS = {
    "years ago",
    "year ago",
    "months ago",
    "month ago",
    "weeks ago",
    "week ago",
    "days ago",
    "day ago",
    "as a child",
    "when i was a child",
    "when i was younger",
    "in childhood",
    "previously",
    "in the past",
    "long ago",
    "last year",
    "last month",
    "last week",
}


CURRENT_MARKERS = {
    "right now",
    "currently",
    "at the moment",
    "right this moment",
    "today",
    "tonight",
    "just now",
    "suddenly",
    "happening now",
    "happening again",
    "again right now",
    "again now",
    "back again",
    "started again",
    "returned",
    "has returned",
    "coming back",
    "comes back",
}


# ---------------------------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Normalize text for deterministic matching."""
    text = (text or "").lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text)


# ---------------------------------------------------------------------------
# NEGATION
# ---------------------------------------------------------------------------

def _is_negated(text: str, phrase: str) -> bool:
    """Detect obvious local negation immediately before a phrase."""
    idx = text.find(phrase)

    if idx < 0:
        return False

    prefix = text[max(0, idx - 80):idx]
    words = _tokenize(prefix)

    return any(word in NEGATION_TERMS for word in words[-8:])


# ---------------------------------------------------------------------------
# HISTORICAL / CURRENT CONTEXT
# ---------------------------------------------------------------------------

def _has_current_recurrence(text: str) -> bool:
    """Return True when the text explicitly says the symptom is current again."""
    return any(marker in text for marker in CURRENT_MARKERS)


def _is_historical(text: str, phrase: str) -> bool:
    """Determine whether a matched phrase refers only to a past event.

    Historical wording is ignored unless the same message explicitly states
    that the symptom has returned, recurred, or is happening now.
    """
    idx = text.find(phrase)

    if idx < 0:
        return False

    # IMPORTANT:
    # Search the complete message for a current recurrence.
    #
    # Example:
    # "I had chest pain six months ago, but it is happening again right now."
    #
    # The historical marker exists, but the recurrence marker means the
    # symptom is active again.
    if _has_current_recurrence(text):
        return False

    context = text[max(0, idx - 120):idx + len(phrase) + 120]

    return any(marker in context for marker in HISTORICAL_MARKERS)


# ---------------------------------------------------------------------------
# MATCHING
# ---------------------------------------------------------------------------

def _find_active_matches(
    normalized: str,
) -> tuple[list[str], list[str]]:
    """Return active emergency categories and matched phrases."""
    detected: list[str] = []
    matched_phrases: list[str] = []

    for category, phrases in EMERGENCY_GROUPS.items():

        for phrase in phrases:

            if phrase not in normalized:
                continue

            # Explicit negation.
            if _is_negated(normalized, phrase):
                continue

            # Historical-only event.
            if _is_historical(normalized, phrase):
                continue

            detected.append(category)
            matched_phrases.append(phrase)

            break

    return detected, matched_phrases


# ---------------------------------------------------------------------------
# PUBLIC SAFETY GATE
# ---------------------------------------------------------------------------

def check_emergency_signs(text: str) -> dict:
    """Run the deterministic emergency safety screen."""
    normalized = _normalize(text)

    if not normalized:
        return {
            "level": "no_emergency_detected",
            "label": "No emergency signs detected",
            "detected_signs": [],
            "matched_phrases": [],
            "message": (
                "No emergency warning signs were detected by the "
                "deterministic safety screen. This does not rule out "
                "a serious condition."
            ),
        }

    detected, matched_phrases = _find_active_matches(normalized)

    if detected:
        return {
            "level": "emergency",
            "label": "Emergency warning signs detected",
            "detected_signs": detected,
            "matched_phrases": matched_phrases,
            "message": (
                "Potential emergency warning signs were detected. "
                "Seek immediate professional medical attention or "
                "contact your local emergency service."
            ),
        }

    return {
        "level": "no_emergency_detected",
        "label": "No emergency signs detected",
        "detected_signs": [],
        "matched_phrases": [],
        "message": (
            "No emergency warning signs were detected by the "
            "deterministic safety screen. This does not rule out "
            "a serious condition."
        ),
    }