from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.assessment_engine import process_answer, start_assessment
from services.ai_service import is_configured, MODEL
from services.conversation_engine import ConversationState

load_dotenv()

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
