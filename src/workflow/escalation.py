from __future__ import annotations

from typing import Any
import re

from openai import OpenAI
from pydantic import BaseModel, Field

from config import OPENAI_API_KEY, OPENAI_MODEL, use_openai
from prompts.escalation_prompt import ESCALATION_PROMPT
from prompts.system_prompt import SYSTEM_PROMPT


class EscalationResult(BaseModel):
    should_escalate: bool = False
    reason: str | None = None
    severity: str = Field(default="low", pattern="^(low|medium|high)$")


class EscalationDetector:
    def __init__(self, sop: dict[str, Any]) -> None:
        self.sop = sop
        self.client = OpenAI(api_key=OPENAI_API_KEY) if use_openai() else None

    def detect(
        self,
        message: str,
        unanswered_count: int = 0,
        context_messages: list[dict[str, str]] | None = None,
    ) -> EscalationResult:
        if unanswered_count > 2:
            return EscalationResult(
                should_escalate=True,
                reason="More than 2 unanswered SOP questions",
                severity="medium",
            )

        if self._is_plain_sop_question(message):
            return EscalationResult()

        if self.client:
            return self._detect_with_openai(message, unanswered_count, context_messages or [])
        return self._detect_locally(message)

    def _detect_with_openai(
        self,
        message: str,
        unanswered_count: int,
        context_messages: list[dict[str, str]],
    ) -> EscalationResult:
        try:
            response = self.client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *context_messages,
                    {"role": "developer", "content": ESCALATION_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Evaluate the latest customer message for escalation. "
                            "Use recent conversation only when needed to understand references.\n\n"
                            f"SOP escalation rules: {self.sop.get('escalate_if', [])}\n"
                            f"Unanswered count: {unanswered_count}\n"
                            f"Latest customer message: {message}"
                        ),
                    },
                ],
                response_format=EscalationResult,
            )
            return response.choices[0].message.parsed
        except Exception:
            return self._detect_locally(message)

    def _detect_locally(self, message: str) -> EscalationResult:
        text = message.lower()
        patterns = [
            (r"\b(angry|furious|frustrated|annoyed|terrible|awful|unhappy)\b", "Customer expressed angry/frustrated sentiment", "high"),
            (r"\b(complaint|complain|refund|bad experience)\b", "Customer made a complaint", "high"),
            (r"\b(human|agent|manager|representative|person)\b", "Customer explicitly requested a human agent", "medium"),
            (r"\b(discount|cheaper|negotiate|bargain|match price)\b", "Customer attempted pricing negotiation", "medium"),
            (r"\b(safe|risk|pregnant|allergy|allergic|side effect|medical|doctor|infection|pain|eligible|eligibility|aftercare|medicine|medication)\b", "Customer asked a medical or aftercare question", "high"),
        ]
        for pattern, reason, severity in patterns:
            if re.search(pattern, text):
                return EscalationResult(should_escalate=True, reason=reason, severity=severity)
        return EscalationResult()

    @staticmethod
    def _is_plain_sop_question(message: str) -> bool:
        text = message.lower()
        escalation_words = (
            r"\b(angry|furious|frustrated|annoyed|terrible|awful|unhappy|"
            r"discount|cheaper|negotiate|bargain|match price|refund|complain|"
            r"complaint|human|agent|manager|representative|person|safe|risk|"
            r"pregnant|allergy|allergic|side effect|medical|doctor|infection|"
            r"pain|eligible|eligibility|aftercare|medicine|medication)\b"
        )
        if re.search(escalation_words, text):
            return False
        return bool(
            re.search(r"\b(services?|treatments?|offer|offered|provide)\b", text)
            or re.search(r"\b(botox|fillers?|consultation|consultations)\b", text)
            or re.search(r"\b(hour|open|time|when)\b", text)
            or re.search(r"\b(book|booking|appointment|schedule)\b", text)
            or re.search(r"\b(cancel|cancellation|reschedule)\b", text)
        )
