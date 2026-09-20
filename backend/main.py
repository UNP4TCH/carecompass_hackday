from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.assessment_engine import process_answer, start_assessment
from services.ai_service import is_configured, MODEL, _is_quota_error, _is_retryable_error
from services.conversation_engine import ConversationState
from services.document_service import simplify_document

load_dotenv()

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(
    title="CareCompass AI API",
    description="Safety-aware AI healthcare navigation prototype.",
    version="1.0.0",
)

conversations: dict[str, ConversationState] = {}

class ConversationStartRequest(BaseModel):
    symptoms: str = Field(min_length=3, max_length=5000)

class ConversationAnswerRequest(BaseModel):
    conversation_id: str
    answer: str = Field(min_length=1, max_length=3000)

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in origins if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _result_payload(conversation_id: str, state: ConversationState, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "conversation_id": conversation_id,
        "stage": result.get("stage"),
        "triage": result.get("triage"),
        "ai_analysis": result.get("ai_analysis"),
        "next_question": result.get("next_question"),
        "answers": result.get("answers", state.answers),
        "final_assessment": result.get("final_assessment"),
        "assistant_message": result.get("assistant_message"),
        "message": result.get("message"),
        "error_code": result.get("error_code"),
        "turn_count": state.turn_count,
        "max_turns": state.max_turns,
    }

@app.get("/")
def root():
    return {"service": "carecompass-api", "version": app.version}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "ai_configured": is_configured(),
        "model": MODEL,
        "active_conversations": len(conversations),
    }

@app.post("/api/conversation/start")
def start_conversation(request: ConversationStartRequest):
    conversation_id = str(uuid.uuid4())
    state, result = start_assessment(request.symptoms)
    conversations[conversation_id] = state
    return _result_payload(conversation_id, state, result)

@app.post("/api/conversation/answer")
def answer_conversation(request: ConversationAnswerRequest):
    state = conversations.get(request.conversation_id)
    if state is None:
        return {"status": "error", "message": "Conversation not found."}
    state, result = process_answer(state, request.answer)
    conversations[request.conversation_id] = state
    return _result_payload(request.conversation_id, state, result)

@app.delete("/api/conversation/{conversation_id}")
def delete_conversation(conversation_id: str):
    conversations.pop(conversation_id, None)
    return {"status": "deleted"}


@app.post("/api/document/simplify")
async def simplify_document_endpoint(
    file: UploadFile = File(...),
):
    """Simplify written instructions from a prescription, discharge note, or medication sheet."""

    # 1. Content type pre-check
    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_MIME_TYPES:
        # Check filename extension as fallback indication
        filename = (file.filename or "").lower()
        if not any(filename.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_code": "unsupported_format",
                    "message": "Unsupported file format. Please upload a JPEG, PNG, or WEBP image.",
                },
            )

    # 2. Read contents and check size
    try:
        contents = await file.read()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "read_error",
                "message": "Unable to read uploaded file. Please try again.",
            },
        )

    if not contents:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "empty_file",
                "message": "The uploaded file is empty. Please select a valid document photo.",
            },
        )

    if len(contents) > MAX_DOCUMENT_SIZE_BYTES:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "file_too_large",
                "message": "File size exceeds 10MB limit. Please upload a smaller image.",
            },
        )

    # 3. Pillow image integrity verification
    import io
    from PIL import Image

    try:
        with Image.open(io.BytesIO(contents)) as img:
            img.verify()
            fmt = (img.format or "").upper()
            if fmt not in {"JPEG", "JPG", "PNG", "WEBP"}:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "error_code": "unsupported_format",
                        "message": "Unsupported file format. Please upload a JPEG, PNG, or WEBP image.",
                    },
                )
            # Map canonical MIME type
            effective_mime = "image/png" if fmt == "PNG" else ("image/webp" if fmt == "WEBP" else "image/jpeg")
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "invalid_image",
                "message": "Invalid or corrupted image. Please upload a clear JPEG, PNG, or WEBP photo.",
            },
        )

    # 4. Check AI service availability
    if not is_configured():
        return JSONResponse(
            status_code=503,
            content={
                "status": "ai_unavailable",
                "error_code": "ai_unavailable",
                "message": "CareCompass document simplification service is temporarily unavailable because the AI service is not configured.",
            },
        )

    # 5. Multimodal extraction
    try:
        result = simplify_document(contents, effective_mime)
        return result.model_dump()
    except Exception as exc:
        if _is_quota_error(exc):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "quota_exceeded",
                    "message": "CareCompass is temporarily busy due to high service demand. Please try again shortly.",
                },
            )

        if _is_retryable_error(exc):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "service_unavailable",
                    "message": "The document analysis service is temporarily unavailable. Please try again in a few moments.",
                },
            )

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "processing_failed",
                "message": "Unable to process document. Please ensure the photo is clear and well-lit, and try again.",
            },
        )

