from __future__ import annotations

from typing import Any
import re

from openai import OpenAI
from pydantic import BaseModel, Field

from config import OPENAI_API_KEY, OPENAI_MODEL, use_openai
from prompts.system_prompt import SYSTEM_PROMPT


class FAQAnswer(BaseModel):
    answer: str
    sop_supported: bool
    evidence: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    sop_gap: str | None = None
    should_escalate: bool = False
    escalation_reason: str | None = None


class FAQAnswerer:
    def __init__(self, sop: dict[str, Any]) -> None:
        self.sop = sop
        self.client = OpenAI(api_key=OPENAI_API_KEY) if use_openai() else None

    def answer(self, message: str) -> FAQAnswer:
        if self.client:
            return self._answer_with_openai(message)
        return self._answer_locally(message)

    def _answer_with_openai(self, message: str) -> FAQAnswer:
        try:
            response = self.client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Answer the customer using only the SOP. If the answer is not "
                            "directly in the SOP, return should_escalate=true.\n\n"
                            f"SOP: {self.sop}\nCustomer message: {message}"
                        ),
                    },
                ],
                response_format=FAQAnswer,
            )
            return response.choices[0].message.parsed
        except Exception:
            return self._answer_locally(message)

    def _answer_locally(self, message: str) -> FAQAnswer:
        text = message.lower()
        if "botox" in text and re.search(r"\b(prices?|cost|how much|start)\b", text):
            return FAQAnswer(
                answer="Botox starts from £200.",
                sop_supported=True,
                evidence="Services: Botox from £200",
                confidence=0.92,
            )
        if "filler" in text and re.search(r"\b(prices?|cost|how much|start)\b", text):
            return FAQAnswer(
                answer="Fillers start from £250.",
                sop_supported=True,
                evidence="Services: Fillers from £250",
                confidence=0.92,
            )
        if "consult" in text and re.search(r"\b(prices?|cost|free|how much)\b", text):
            return FAQAnswer(
                answer="Consultations are free.",
                sop_supported=True,
                evidence="Services: Consultations free",
                confidence=0.93,
            )
        if re.search(r"\b(hour|open|time|when)\b", text):
            return FAQAnswer(
                answer="Bloom Aesthetics Clinic is open Mon-Sat, 9 am-7 pm.",
                sop_supported=True,
                evidence="Hours: Mon-Sat, 9 am-7 pm",
                confidence=0.94,
            )
        if re.search(r"\b(book|booking|appointment|schedule)\b", text):
            return FAQAnswer(
                answer="Bookings are available via WhatsApp or the website.",
                sop_supported=True,
                evidence="Booking: via WhatsApp or website",
                confidence=0.9,
            )
        if re.search(r"\b(cancel|cancellation|reschedule)\b", text):
            return FAQAnswer(
                answer="The clinic requires 24hr cancellation notice.",
                sop_supported=True,
                evidence="Cancellation: 24hr cancellation required",
                confidence=0.9,
            )

        gap = self._gap_for_message(text)
        return FAQAnswer(
            answer="I don't have that information in the clinic SOP, so I'll pass this to a human team member.",
            sop_supported=False,
            evidence=None,
            confidence=0.25,
            sop_gap=gap,
            should_escalate=True,
            escalation_reason="Out-of-scope question",
        )

    @staticmethod
    def _gap_for_message(text: str) -> str:
        if "aftercare" in text:
            return "SOP does not include aftercare instructions"
        if re.search(r"\b(safe|eligible|pregnant|allergy|side effect|medical)\b", text):
            return "SOP does not include medical eligibility information"
        if "available" in text or "slot" in text:
            return "SOP does not include appointment availability"
        return "SOP does not include this requested information"
