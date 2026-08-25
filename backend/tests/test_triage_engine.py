from services.triage_engine import check_emergency_signs


def test_emergency_chest_pain():
    result = check_emergency_signs("I have severe chest pain and pressure in my chest")
    assert result["level"] == "emergency"


def test_negated_chest_pain_is_not_flagged():
    result = check_emergency_signs("I do not have chest pain")
    assert result["level"] == "no_emergency_detected"


def test_breathing_emergency():
    result = check_emergency_signs("I am struggling to breathe")
    assert result["level"] == "emergency"
