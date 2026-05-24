from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_name: str | None = None
    email: str | None = None
    service_interest: str | None = None
    booking_preference: str | None = None
    urgency: str | None = None
    lead_score: float = 0.0
    intent_confidence: float = 0.0
    unanswered_count: int = 0
    sop_gaps: list[str] = Field(default_factory=list)
    escalation_reasons: list[str] = Field(default_factory=list)
    lead_saved: bool = False
    messages: list[ConversationMessage] = Field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(ConversationMessage(role=role, content=content))

    def transcript(self) -> list[dict[str, Any]]:
        return [message.model_dump() for message in self.messages]

    def recent_openai_messages(self, max_turns: int = 8, exclude_latest_user: bool = True) -> list[dict[str, str]]:
        messages = [message for message in self.messages if message.role in {"user", "assistant"}]
        if exclude_latest_user and messages and messages[-1].role == "user":
            messages = messages[:-1]

        max_messages = max_turns * 2
        recent = messages[-max_messages:]
        return [{"role": message.role, "content": message.content} for message in recent]


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def create(self) -> SessionState:
        session = SessionState()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)
