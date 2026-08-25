from services.triage_engine import check_emergency_signs


def test_active_breathing_emergency():
    result = check_emergency_signs(
        "I am struggling to breathe right now."
    )

    assert result["level"] == "emergency"
    assert "breathing" in result["detected_signs"]


def test_active_chest_emergency():
    result = check_emergency_signs(
        "I have severe chest pain."
    )

    assert result["level"] == "emergency"
    assert "severe_chest_symptoms" in result["detected_signs"]


def test_active_stroke_warning():
    result = check_emergency_signs(
        "My speech is suddenly slurred."
    )

    assert result["level"] == "emergency"
    assert "stroke" in result["detected_signs"]


def test_late_emergency_information():
    result = check_emergency_signs(
        "I started with a mild headache, but actually "
        "I am now having trouble speaking."
    )

    assert result["level"] == "emergency"
    assert "stroke" in result["detected_signs"]


def test_negated_chest_pain():
    result = check_emergency_signs(
        "I don't have chest pain."
    )

    assert result["level"] == "no_emergency_detected"


def test_negated_breathing_problem():
    result = check_emergency_signs(
        "I am not having difficulty breathing."
    )

    assert result["level"] == "no_emergency_detected"


def test_historical_event():
    result = check_emergency_signs(
        "I had a seizure years ago."
    )

    assert result["level"] == "no_emergency_detected"


def test_historical_chest_pain():
    result = check_emergency_signs(
        "I had chest pain six months ago."
    )

    assert result["level"] == "no_emergency_detected"


def test_historical_but_current_again():
    result = check_emergency_signs(
        "I had chest pain six months ago, "
        "but it is happening again right now."
    )

    assert result["level"] == "emergency"


def test_multiple_emergency_signs():
    result = check_emergency_signs(
        "I have severe chest pain and I am struggling to breathe."
    )

    assert result["level"] == "emergency"

    assert "severe_chest_symptoms" in result["detected_signs"]
    assert "breathing" in result["detected_signs"]


def test_case_and_punctuation_variations():
    result = check_emergency_signs(
        "I CAN'T BREATHE!!!"
    )

    assert result["level"] == "emergency"


def test_empty_input():
    result = check_emergency_signs("")

    assert result["level"] == "no_emergency_detected"


def test_normal_symptoms_do_not_trigger_emergency():
    result = check_emergency_signs(
        "I have a mild headache and feel tired."
    )

    assert result["level"] == "no_emergency_detected"