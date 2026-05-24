from __future__ import annotations

from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from config import OPENAI_API_KEY, OPENAI_MODEL, use_openai
from prompts.summary_prompt import SUMMARY_PROMPT
from prompts.system_prompt import SYSTEM_PROMPT


class ConversationSummary(BaseModel):
    customer_intent: str
    key_details_collected: dict[str, Any]
    sop_gaps_identified: list[str]
    recommended_next_action: str


class SummaryGenerator:
    def __init__(self, sop: dict[str, Any]) -> None:
        self.sop = sop
        self.client = OpenAI(api_key=OPENAI_API_KEY) if use_openai() else None

    def generate(self, session) -> ConversationSummary:
        if self.client:
            try:
                response = self.client.beta.chat.completions.parse(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "developer", "content": SUMMARY_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                f"SOP: {self.sop}\n"
                                f"Session: {session.model_dump()}"
                            ),
                        },
                    ],
                    response_format=ConversationSummary,
                )
                return response.choices[0].message.parsed
            except Exception:
                pass
        return self._generate_locally(session)

    def _generate_locally(self, session) -> ConversationSummary:
        service = session.service_interest or "clinic services"
        if session.lead_score > 0.6:
            intent = f"Customer wanted {service} pricing or booking information"
        else:
            intent = "Customer asked general clinic support questions"

        if session.escalation_reasons:
            action = "Human agent should review the escalation and follow up with the customer."
        elif session.email:
            if session.booking_preference == "WhatsApp":
                action = "Human agent should follow up on WhatsApp to schedule the consultation."
            elif session.booking_preference == "Website":
                action = "Human agent should direct the customer to the website booking flow."
            else:
                action = "Human agent should follow up to schedule the consultation."
        else:
            action = "No lead was fully captured; continue the conversation if the customer returns."

        return ConversationSummary(
            customer_intent=intent,
            key_details_collected={
                "name": session.customer_name,
                "email": session.email,
                "service_interest": session.service_interest,
                "booking_preference": session.booking_preference,
                "urgency": session.urgency,
            },
            sop_gaps_identified=session.sop_gaps,
            recommended_next_action=action,
        )
