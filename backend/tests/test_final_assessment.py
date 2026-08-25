from services import final_assessment


def test_invalid_ai_values_are_normalized(monkeypatch):
    def fake_generate(**kwargs):
        return {
            "summary": "Test",
            "urgency": "something_invalid",
            "recommended_action": "Test action",
            "why": "Test reason",
            "warning_signs": "not a list",
            "care_level": "invalid",
        }

    monkeypatch.setattr(
        final_assessment,
        "generate_final_assessment",
        fake_generate,
    )

    result = final_assessment.build_final_assessment(
        symptoms="mild headache",
        known_information={},
        answers={},
        safety_flags=[],
    )

    assert result["urgency"] == "routine_follow_up"
    assert result["care_level"] == "routine"
    assert result["warning_signs"] == []


def test_safety_flags_override_ai(monkeypatch):
    def fake_generate(**kwargs):
        return {
            "summary": "Everything appears fine.",
            "urgency": "self_care_monitoring",
            "recommended_action": "Rest.",
            "why": "The symptoms seem mild.",
            "warning_signs": [],
            "care_level": "self_care",
        }

    monkeypatch.setattr(
        final_assessment,
        "generate_final_assessment",
        fake_generate,
    )

    result = final_assessment.build_final_assessment(
        symptoms="headache",
        known_information={},
        answers={},
        safety_flags=["stroke"],
    )

    assert result["urgency"] == "emergency"
    assert result["care_level"] == "emergency"
    assert "immediate professional" in (
        result["recommended_action"]
    )


def test_normal_result_is_preserved(monkeypatch):
    def fake_generate(**kwargs):
        return {
            "summary": "Mild headache.",
            "urgency": "self_care_monitoring",
            "recommended_action": "Monitor symptoms.",
            "why": "No concerning information was provided.",
            "warning_signs": ["worsening symptoms"],
            "care_level": "self_care",
        }

    monkeypatch.setattr(
        final_assessment,
        "generate_final_assessment",
        fake_generate,
    )

    result = final_assessment.build_final_assessment(
        symptoms="mild headache",
        known_information={
            "duration": "this morning",
            "severity": "mild",
        },
        answers={},
        safety_flags=[],
    )

    assert result["urgency"] == "self_care_monitoring"
    assert result["care_level"] == "self_care"
    assert result["summary"] == "Mild headache."