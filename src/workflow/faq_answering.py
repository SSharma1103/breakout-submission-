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

    def answer(self, message: str, context_messages: list[dict[str, str]] | None = None) -> FAQAnswer:
        known_answer = self._answer_known_sop_fact(message)
        if known_answer:
            return known_answer
        if self.client:
            return self._answer_with_openai(message, context_messages or [])
        return self._answer_locally(message)

    def _answer_with_openai(self, message: str, context_messages: list[dict[str, str]]) -> FAQAnswer:
        try:
            response = self.client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *context_messages,
                    {
                        "role": "user",
                        "content": (
                            "Answer the latest customer message. Use conversation context "
                            "only to resolve references like 'that' or 'it'. Use the SOP "
                            "only for factual answers. If the answer is not directly in "
                            "the SOP, return should_escalate=true.\n\n"
                            f"SOP: {self.sop}\nLatest customer message: {message}"
                        ),
                    },
                ],
                response_format=FAQAnswer,
            )
            return response.choices[0].message.parsed
        except Exception:
            return self._answer_locally(message)

    def _answer_locally(self, message: str) -> FAQAnswer:
        known_answer = self._answer_known_sop_fact(message)
        if known_answer:
            return known_answer

        text = message.lower()
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

    def _answer_known_sop_fact(self, message: str) -> FAQAnswer | None:
        text = message.lower()
        if re.search(r"\b(services?|treatments?|offer|offered|provide)\b", text):
            services = ", ".join(self.sop["services"].keys())
            return FAQAnswer(
                answer=f"Bloom Aesthetics Clinic offers {services}.",
                sop_supported=True,
                evidence=f"Services: {services}",
                confidence=0.91,
            )
        if "botox" in text:
            return FAQAnswer(
                answer="Botox starts from £200.",
                sop_supported=True,
                evidence="Services: Botox from £200",
                confidence=0.92,
            )
        if "filler" in text:
            return FAQAnswer(
                answer="Fillers start from £250.",
                sop_supported=True,
                evidence="Services: Fillers from £250",
                confidence=0.92,
            )
        if "consult" in text:
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

        return None

    @staticmethod
    def _gap_for_message(text: str) -> str:
        if "aftercare" in text:
            return "SOP does not include aftercare instructions"
        if re.search(r"\b(safe|eligible|pregnant|allergy|side effect|medical)\b", text):
            return "SOP does not include medical eligibility information"
        if "available" in text or "slot" in text:
            return "SOP does not include appointment availability"
        return "SOP does not include this requested information"
