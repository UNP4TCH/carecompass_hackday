"""Document simplification service for CareCompass (Phase 3).

Extracts and translates written medication instructions from prescriptions,
discharge notes, and medication instruction sheets into plain language.

Strict safety constraints:
- Reads ONLY visible text.
- Never diagnoses, recommends, alters, or evaluates medication suitability.
- Never guesses unreadable handwriting or infers missing data.
- Unclear or missing fields are explicitly marked as "Could not be read clearly"
  or "Not specified in document".
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field

from services import ai_service

logger = logging.getLogger("carecompass.document_service")

MANDATORY_DISCLAIMER = (
    "CareCompass simplifies information written on your document. "
    "It does not replace instructions from your doctor or pharmacist."
)


# ---------------------------------------------------------------------------
# STRUCTURED DATA SCHEMAS
# ---------------------------------------------------------------------------

class MedicationItem(BaseModel):
    name: str = Field(
        description="Exact medication name as written on the document, or 'Could not be read clearly'."
    )
    strength: str = Field(
        default="Not specified in document",
        description="Strength e.g. '500 mg', '10 mg/5 mL', or 'Could not be read clearly' / 'Not specified in document'."
    )
    dosage: str = Field(
        default="Not specified in document",
        description="Dosage per take e.g. '1 tablet', '2 puffs', or 'Could not be read clearly' / 'Not specified in document'."
    )
    frequency: str = Field(
        default="Not specified in document",
        description="Plain-language frequency e.g. '2 times a day', 'Once daily', or 'Could not be read clearly' / 'Not specified in document'."
    )
    timing: str = Field(
        default="Not specified in document",
        description="Timing instructions if stated e.g. 'Morning and evening', 'At bedtime', or 'Not specified in document'."
    )
    duration: str = Field(
        default="Not specified in document",
        description="Duration e.g. '5 days', 'Until finished', or 'Could not be read clearly' / 'Not specified in document'."
    )
    route: str = Field(
        default="Not specified in document",
        description="Route/method of use e.g. 'By mouth', 'Apply topically to skin', or 'Not specified in document'."
    )
    food_instructions: str = Field(
        default="Not specified in document",
        description="Food-related instructions e.g. 'After food', 'On an empty stomach', or 'Not specified in document'."
    )
    other_instructions: str = Field(
        default="None",
        description="Other explicit medication instructions written on document e.g. 'Take with full glass of water'."
    )
    warnings: str = Field(
        default="None",
        description="Explicit warnings/precautions written for this medication on document e.g. 'Do not drive', 'Avoid alcohol'."
    )
    is_readable: bool = Field(
        default=True,
        description="False if the medication or its directions are blurry, illegible, or ambiguous."
    )
    notes: str = Field(
        default="",
        description="Notes regarding handwriting, legibility, or ambiguities if applicable."
    )


class DocumentSimplificationResult(BaseModel):
    status: str = Field(
        default="success",
        description="Status: 'success', 'unreadable', 'no_medications_found', or 'not_a_medical_document'."
    )
    document_type: str = Field(
        default="prescription",
        description="Document type: 'prescription', 'discharge_note', 'medication_sheet', or 'other'."
    )
    is_legible: bool = Field(
        default=True,
        description="Whether the document is legible enough to reliably extract medication instructions."
    )
    legibility_summary: str = Field(
        default="",
        description="Assessment of document legibility or reasons if blurry, cropped, or ambiguous."
    )
    medications: list[MedicationItem] = Field(
        default_factory=list,
        description="List of medications extracted from the document."
    )
    general_instructions: list[str] = Field(
        default_factory=list,
        description="Explicit general non-medication care/follow-up instructions written on document."
    )
    warnings_and_precautions: list[str] = Field(
        default_factory=list,
        description="Explicit general warnings or precautions written on the document."
    )
    disclaimer: str = Field(
        default=MANDATORY_DISCLAIMER,
        description="Mandatory patient disclaimer."
    )


# ---------------------------------------------------------------------------
# PROMPT DEFINITION
# ---------------------------------------------------------------------------

SIMPLIFIER_PROMPT = """
You are the document information-simplification component of CareCompass.

Your job is to read an uploaded image of a prescription, hospital discharge note,
or medication instruction sheet, and translate its written instructions into clear,
accessible, plain language for the patient.

CRITICAL SAFETY & MEDICAL CONSTRAINTS:
1. You are NOT a doctor, pharmacist, or diagnostic system.
2. NEVER diagnose the patient or infer what condition they have based on medications.
3. NEVER recommend starting, stopping, increasing, decreasing, or altering any medication.
4. NEVER recommend drug substitutions or suggest alternative treatments.
5. NEVER invent, assume, or extrapolate any information that is not visibly written on the document.
6. If handwriting or text is blurry, smeared, truncated, or ambiguous:
   - Mark the corresponding field as "Could not be read clearly".
   - Do NOT guess what the doctor or author intended.
   - Example: If a dosage looks like "1" or "2" tablets, write "Could not be read clearly".
7. If a detail is simply not mentioned anywhere on the document:
   - Mark the field as "Not specified in document".
8. Preserve medication names and numbers (mg, ml, days, quantities) exactly as written.
9. Translate medical shorthand and abbreviations into plain English:
   - "PO" / "p.o." -> "By mouth"
   - "OD" / "q.d." -> "Once daily"
   - "BD" / "BID" / "1-0-1" -> Frequency: "2 times a day", Timing: "Morning and evening"
   - "TDS" / "TID" / "1-1-1" -> Frequency: "3 times a day", Timing: "Morning, afternoon, and night"
   - "QID" / "1-1-1-1" -> Frequency: "4 times a day"
   - "q8h" -> Frequency: "Every 8 hours"
   - "q4h PRN" -> Frequency: "Every 4 hours as needed"
   - "SOS" / "PRN" -> "As needed"
   - "PC" / "p.c." -> "After meals / after food"
   - "AC" / "a.c." -> "Before meals"
   - "HS" / "h.s." -> "At bedtime"
   - "Stat" -> "Immediately (single dose)"
10. If the image is not a prescription, hospital discharge note, or medication sheet
    (e.g., a selfie, scenery, non-medical document):
    - Set status="not_a_medical_document"
    - Set is_legible=false
    - Leave medications=[]
11. If the document is too blurry, dark, low-resolution, or damaged to read reliably:
    - Set status="unreadable"
    - Set is_legible=false
    - Provide a polite explanation in legibility_summary
12. If the document is readable but contains NO medications or prescription instructions:
    - Set status="no_medications_found"
    - Leave medications=[]
"""


# ---------------------------------------------------------------------------
# GEMINI MULTIMODAL INVOCATION
# ---------------------------------------------------------------------------

def _call_gemini_multimodal(
    image_bytes: bytes,
    mime_type: str,
) -> DocumentSimplificationResult:
    """Send image and prompt to Gemini with structured output validation and retry handling."""

    client = ai_service._require_client()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    last_error: Exception | None = None

    for attempt in range(ai_service.MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=ai_service.MODEL,
                contents=[image_part, SIMPLIFIER_PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DocumentSimplificationResult,
                    temperature=0.1,
                ),
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = DocumentSimplificationResult.model_validate_json(response.text)
            # Ensure mandatory disclaimer is always present
            result.disclaimer = MANDATORY_DISCLAIMER
            return result

        except Exception as exc:
            last_error = exc
            if ai_service._is_quota_error(exc):
                logger.error("Gemini quota exhausted during document simplification: %s", exc)
                raise

            if ai_service._is_retryable_error(exc) and attempt < ai_service.MAX_RETRIES:
                logger.warning(
                    "Retryable error on attempt %d for document simplification: %s",
                    attempt + 1,
                    exc,
                )
                time.sleep(ai_service.RETRY_DELAYS[attempt])
                continue

            raise

    if last_error is not None:
        raise last_error

    raise RuntimeError("Document simplification failed without returning an exception.")


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def simplify_document(
    image_bytes: bytes,
    mime_type: str,
) -> DocumentSimplificationResult:
    """Validate image bytes and extract simplified medication instructions.

    Returns a validated DocumentSimplificationResult.
    """
    if not ai_service.is_configured():
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    # Image validation
    if not image_bytes:
        raise ValueError("Image bytes are empty.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
            fmt = (img.format or "").upper()
            if fmt not in {"JPEG", "JPG", "PNG", "WEBP"}:
                raise ValueError(f"Unsupported image format: {fmt}")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Invalid or corrupted image file.") from exc

    return _call_gemini_multimodal(image_bytes=image_bytes, mime_type=mime_type)
