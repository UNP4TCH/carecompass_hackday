from services.navigation_engine import build_care_navigation


def test_self_care_navigation():
    result = build_care_navigation(
        urgency="self_care_monitoring",
        care_level="self_care",
    )

    assert result["level"] == "self_care"
    assert result["label"] == "Self-care & monitoring"
    assert result["timeframe"]
    assert result["setting"]
    assert result["action"]
    assert result["escalation"]


def test_routine_navigation():
    result = build_care_navigation(
        urgency="routine_follow_up",
        care_level="routine",
    )

    assert result["level"] == "routine"
    assert "Routine" in result["label"]


def test_urgent_navigation():
    result = build_care_navigation(
        urgency="prompt_medical_attention",
        care_level="urgent",
    )

    assert result["level"] == "urgent"
    assert result["timeframe"]
    assert result["setting"]


def test_emergency_navigation():
    result = build_care_navigation(
        urgency="emergency",
        care_level="emergency",
    )

    assert result["level"] == "emergency"
    assert result["timeframe"] == "Now"


def test_safety_flags_override_everything():
    result = build_care_navigation(
        urgency="self_care_monitoring",
        care_level="self_care",
        safety_flags=["stroke"],
    )

    assert result["level"] == "emergency"
    assert result["label"] == "Immediate attention"
    assert result["timeframe"] == "Now"


def test_urgency_fallback_mapping():
    result = build_care_navigation(
        urgency="routine_follow_up",
        care_level="unknown",
    )

    assert result["level"] == "routine"