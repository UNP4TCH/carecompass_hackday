"""State management for one CareCompass assessment.

The conversation state keeps two related but distinct representations:

1. Conversation history
   - What the user actually said.
   - Preserved for traceability and final assessment context.

2. Current case knowledge
   - The latest structured understanding of the case.
   - Can be updated when the user corrects or clarifies previous information.

The state layer does not perform medical reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ConversationState:
    # ------------------------------------------------------------------
    # CORE CASE
    # ------------------------------------------------------------------

    original_symptoms: str = ""

    # Structured understanding of the current case.
    known_information: dict[str, Any] = field(default_factory=dict)

    # Raw answers indexed by question ID.
    # These preserve conversation history.
    answers: dict[str, str] = field(default_factory=dict)

    # Complete question/answer history.
    question_history: list[dict[str, Any]] = field(
        default_factory=list
    )

    # Currently active question.
    current_question: dict[str, str] | None = None

    # Deterministic safety flags accumulated during the assessment.
    safety_flags: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # PROGRESS
    # ------------------------------------------------------------------

    turn_count: int = 0
    max_turns: int = 7
    completed: bool = False

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    # ------------------------------------------------------------------
    # COMPATIBILITY
    # ------------------------------------------------------------------

    @property
    def symptoms(self) -> str:
        """Backward-compatible alias used by older code."""
        return self.original_symptoms

    # ------------------------------------------------------------------
    # TIMESTAMP
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """Update the state's modification timestamp."""
        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    # ------------------------------------------------------------------
    # QUESTION MANAGEMENT
    # ------------------------------------------------------------------

    def set_question(
        self,
        question: str,
        rationale: str = "",
    ) -> dict:

        if self.completed:
            raise RuntimeError(
                "Cannot create a question for a completed assessment."
            )

        question = (question or "").strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        if self.turn_count >= self.max_turns:
            raise RuntimeError(
                "Maximum assessment turns reached."
            )

        question_id = (
            f"q_{len(self.question_history) + 1}"
        )

        payload = {
            "completed": False,
            "question_id": question_id,
            "question": question,
        }

        self.current_question = payload

        self.question_history.append(
            {
                **payload,
                "rationale": rationale,
                "answered": False,
            }
        )

        self.touch()

        return payload

    def record_answer(
        self,
        answer: str,
    ) -> None:

        if self.completed:
            raise RuntimeError(
                "Cannot record an answer for a completed assessment."
            )

        if not self.current_question:
            raise RuntimeError(
                "There is no active question."
            )

        answer = (answer or "").strip()

        if not answer:
            raise ValueError(
                "Answer cannot be empty."
            )

        question_id = (
            self.current_question["question_id"]
        )

        # Preserve the raw answer.
        self.answers[question_id] = answer

        # Update the corresponding history entry.
        for item in reversed(self.question_history):
            if item["question_id"] == question_id:
                item["answered"] = True
                item["answer"] = answer
                break

        self.current_question = None
        self.turn_count += 1

        self.touch()

    def asked_questions(self) -> list[str]:
        """Return every question asked so far."""
        return [
            item["question"]
            for item in self.question_history
        ]

    # ------------------------------------------------------------------
    # CASE KNOWLEDGE
    # ------------------------------------------------------------------

    def set_known_information(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set the current structured value for a case field.

        This represents the latest known state rather than conversation
        history.
        """
        key = (key or "").strip()

        if not key:
            raise ValueError(
                "Known-information key cannot be empty."
            )

        self.known_information[key] = value
        self.touch()

    def update_known_information(
        self,
        updates: dict[str, Any],
    ) -> None:
        """Update multiple current case fields."""
        if not updates:
            return

        for key, value in updates.items():
            if key:
                self.known_information[key] = value

        self.touch()

    def append_known_information(
        self,
        key: str,
        values: list[Any] | tuple[Any, ...],
    ) -> None:
        """Append information to a list-based case field.

        Useful for facts or newly discovered symptoms where preserving
        multiple items is appropriate.
        """
        if not values:
            return

        existing = self.known_information.setdefault(
            key,
            [],
        )

        if not isinstance(existing, list):
            existing = [existing]
            self.known_information[key] = existing

        for value in values:
            if value not in existing:
                existing.append(value)

        self.touch()

    # ------------------------------------------------------------------
    # SAFETY
    # ------------------------------------------------------------------

    def add_safety_flags(
        self,
        flags: list[str] | tuple[str, ...],
    ) -> None:
        """Add deterministic safety flags without duplicates."""
        changed = False

        for flag in flags:
            if flag and flag not in self.safety_flags:
                self.safety_flags.append(flag)
                changed = True

        if changed:
            self.touch()

    # ------------------------------------------------------------------
    # COMPLETION
    # ------------------------------------------------------------------

    def complete(self) -> None:
        """Mark the assessment as complete."""
        self.current_question = None
        self.completed = True
        self.touch()


# ----------------------------------------------------------------------
# FACTORY
# ----------------------------------------------------------------------

def create_conversation(
    symptoms: str,
) -> ConversationState:
    """Create a new assessment state."""
    return ConversationState(
        original_symptoms=(symptoms or "").strip()
    )
