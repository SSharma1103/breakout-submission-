from __future__ import annotations

from typing import Any
import re

from openai import OpenAI
from pydantic import BaseModel, Field

from config import OPENAI_API_KEY, OPENAI_MODEL, use_openai
from prompts.system_prompt import SYSTEM_PROMPT


class IntentResult(BaseModel):
    intent: str = "general_question"
    service_interest: str | None = None
    intent_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    lead_score: float = Field(default=0.0, ge=0.0, le=1.0)


class IntentClassifier:
    def __init__(self, sop: dict[str, Any]) -> None:
        self.sop = sop
        self.client = OpenAI(api_key=OPENAI_API_KEY) if use_openai() else None

    def classify(self, message: str) -> IntentResult:
        if self.client:
            return self._classify_with_openai(message)
        return self._classify_locally(message)

    def _classify_with_openai(self, message: str) -> IntentResult:
        try:
            response = self.client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Classify the customer's latest message. Keep intent_confidence "
                            "separate from lead_score.\n\n"
                            f"SOP: {self.sop}\nMessage: {message}"
                        ),
                    },
                ],
                response_format=IntentResult,
            )
            return response.choices[0].message.parsed
        except Exception:
            return self._classify_locally(message)

    def _classify_locally(self, message: str) -> IntentResult:
        text = message.lower()
        service_interest = None
        if "botox" in text:
            service_interest = "Botox"
        elif "filler" in text:
            service_interest = "Fillers"
        elif "consult" in text:
            service_interest = "Consultations"

        if re.search(r"\b(book|appointment|schedule|whatsapp|website)\b", text):
            return IntentResult(
                intent="pricing_and_booking" if service_interest else "booking",
                service_interest=service_interest,
                intent_confidence=0.88,
                lead_score=0.75,
            )
        if re.search(r"\b(prices?|cost|how much|start)\b", text):
            return IntentResult(
                intent="pricing_and_booking",
                service_interest=service_interest,
                intent_confidence=0.9,
                lead_score=0.65 if service_interest else 0.45,
            )
        if re.search(r"\b(email|@|this week|today|tomorrow)\b", text):
            return IntentResult(
                intent="lead_details",
                service_interest=service_interest,
                intent_confidence=0.72,
                lead_score=0.7,
            )
        return IntentResult(service_interest=service_interest)
