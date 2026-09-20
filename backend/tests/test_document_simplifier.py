import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app
from services.document_service import (
    DocumentSimplificationResult,
    MedicationItem,
    MANDATORY_DISCLAIMER,
)

client = TestClient(app)


def _make_test_image(fmt="JPEG") -> bytes:
    """Create a minimal valid image in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="white")
    img.save(buf, format=fmt)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------------------------

def test_unsupported_file_format():
    """Files that are not JPEG, PNG, or WEBP must be rejected with 400."""
    response = client.post(
        "/api/document/simplify",
        files={"file": ("notes.txt", b"Paracetamol 500mg daily", "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "unsupported_format"
    assert "Unsupported file format" in data["message"]


def test_empty_file():
    """Zero-byte uploads must be rejected with 400."""
    response = client.post(
        "/api/document/simplify",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "empty_file"


def test_oversized_file(monkeypatch):
    """Files exceeding 10MB limit must be rejected with 400."""
    # Monkeypatch limit to small number for quick testing
    monkeypatch.setattr("main.MAX_DOCUMENT_SIZE_BYTES", 1024)
    big_payload = b"x" * 2048
    response = client.post(
        "/api/document/simplify",
        files={"file": ("large.jpg", big_payload, "image/jpeg")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "file_too_large"


def test_corrupt_or_fake_image():
    """Files with image MIME type but invalid image contents must be rejected."""
    fake_image = b"This is not a real JPEG image header"
    response = client.post(
        "/api/document/simplify",
        files={"file": ("fake.jpg", fake_image, "image/jpeg")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "invalid_image"


def test_ai_unavailable_handling(monkeypatch):
    """When Gemini is not configured, endpoint must return 503 ai_unavailable."""
    monkeypatch.setattr("main.is_configured", lambda: False)
    valid_image = _make_test_image("JPEG")

    response = client.post(
        "/api/document/simplify",
        files={"file": ("prescription.jpg", valid_image, "image/jpeg")},
    )
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "ai_unavailable"
    assert data["error_code"] == "ai_unavailable"


def test_valid_document_simplification_success(monkeypatch):
    """Valid image upload produces structured plain-language medication extraction."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    mock_result = DocumentSimplificationResult(
        status="success",
        document_type="prescription",
        is_legible=True,
        legibility_summary="The prescription is clear and legible.",
        medications=[
            MedicationItem(
                name="Amoxicillin",
                strength="500 mg",
                dosage="1 capsule",
                frequency="3 times a day",
                timing="Morning, afternoon, and evening",
                duration="7 days",
                route="By mouth",
                food_instructions="Take with or after food",
                other_instructions="Finish the entire course",
                warnings="None",
                is_readable=True,
            ),
            MedicationItem(
                name="Paracetamol",
                strength="650 mg",
                dosage="1 tablet",
                frequency="As needed (up to 3 times a day)",
                timing="When in pain or fever",
                duration="5 days as needed",
                route="By mouth",
                food_instructions="After food",
                other_instructions="Take with a full glass of water",
                warnings="Do not exceed 3 grams daily",
                is_readable=True,
            ),
        ],
        general_instructions=["Drink plenty of fluids and rest."],
        warnings_and_precautions=["Do not exceed the recommended dose."],
        disclaimer=MANDATORY_DISCLAIMER,
    )

    monkeypatch.setattr(
        "main.simplify_document",
        lambda contents, mime: mock_result,
    )

    valid_image = _make_test_image("PNG")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("rx.png", valid_image, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_legible"] is True
    assert len(data["medications"]) == 2
    assert data["medications"][0]["name"] == "Amoxicillin"
    assert data["medications"][0]["frequency"] == "3 times a day"
    assert data["medications"][0]["food_instructions"] == "Take with or after food"
    assert data["disclaimer"] == MANDATORY_DISCLAIMER


def test_unreadable_or_blurry_document(monkeypatch):
    """When document is blurry or illegible, model flags it and does not invent details."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    mock_result = DocumentSimplificationResult(
        status="unreadable",
        document_type="prescription",
        is_legible=False,
        legibility_summary="The handwriting is heavily smudged and out of focus.",
        medications=[
            MedicationItem(
                name="Could not be read clearly",
                strength="Could not be read clearly",
                dosage="Could not be read clearly",
                frequency="Could not be read clearly",
                timing="Not specified in document",
                duration="Could not be read clearly",
                route="Not specified in document",
                food_instructions="Not specified in document",
                is_readable=False,
                notes="Text is blurry across the medication lines.",
            )
        ],
        disclaimer=MANDATORY_DISCLAIMER,
    )

    monkeypatch.setattr(
        "main.simplify_document",
        lambda contents, mime: mock_result,
    )

    valid_image = _make_test_image("JPEG")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("blurry.jpg", valid_image, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unreadable"
    assert data["is_legible"] is False
    assert "smudged" in data["legibility_summary"]
    # Verify unreadable fields are not fabricated
    med = data["medications"][0]
    assert med["name"] == "Could not be read clearly"
    assert med["dosage"] == "Could not be read clearly"


def test_missing_fields_not_fabricated(monkeypatch):
    """Verify that unstated fields remain 'Not specified in document' and are not invented."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    mock_result = DocumentSimplificationResult(
        status="success",
        document_type="discharge_note",
        is_legible=True,
        legibility_summary="Document is readable.",
        medications=[
            MedicationItem(
                name="Atorvastatin",
                strength="20 mg",
                dosage="1 tablet",
                frequency="Once daily",
                timing="At bedtime",
                duration="Not specified in document",
                route="By mouth",
                food_instructions="Not specified in document",
                other_instructions="None",
                warnings="None",
                is_readable=True,
            )
        ],
        disclaimer=MANDATORY_DISCLAIMER,
    )

    monkeypatch.setattr(
        "main.simplify_document",
        lambda contents, mime: mock_result,
    )

    valid_image = _make_test_image("WEBP")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("rx.webp", valid_image, "image/webp")},
    )

    assert response.status_code == 200
    data = response.json()
    med = data["medications"][0]
    assert med["duration"] == "Not specified in document"
    assert med["food_instructions"] == "Not specified in document"


def test_gemini_quota_error_handled_gracefully(monkeypatch):
    """Verify quota exhausted errors return 503 without leaking stack traces."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    def _raise_quota(contents, mime):
        raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")

    monkeypatch.setattr("main.simplify_document", _raise_quota)

    valid_image = _make_test_image("JPEG")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("rx.jpg", valid_image, "image/jpeg")},
    )

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "quota_exceeded"
    assert "high service demand" in data["message"]
    # Ensure no stack trace in response
    assert "traceback" not in str(data).lower()


def test_gemini_retryable_service_error(monkeypatch):
    """Verify transient 503 service unavailable errors return clean user message."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    def _raise_transient(contents, mime):
        raise RuntimeError("503 UNAVAILABLE: backend service unavailable")

    monkeypatch.setattr("main.simplify_document", _raise_transient)

    valid_image = _make_test_image("JPEG")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("rx.jpg", valid_image, "image/jpeg")},
    )

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "service_unavailable"
    assert "temporarily unavailable" in data["message"]


def test_generic_failure_does_not_leak_stack_trace(monkeypatch):
    """Any unexpected internal failure returns clean 500 without leaking stack traces."""
    monkeypatch.setattr("main.is_configured", lambda: True)

    def _raise_secret(contents, mime):
        raise ValueError("Secret internal database password failure in /var/secrets/key")

    monkeypatch.setattr("main.simplify_document", _raise_secret)

    valid_image = _make_test_image("JPEG")
    response = client.post(
        "/api/document/simplify",
        files={"file": ("rx.jpg", valid_image, "image/jpeg")},
    )

    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "processing_failed"
    assert "Secret" not in str(data)
    assert "/var/secrets" not in str(data)
