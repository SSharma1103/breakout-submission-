from __future__ import annotations

import re

from pydantic import BaseModel, Field


class Lead(BaseModel):
    name: str
    email: str
    service_interest: str | None = None
    booking_preference: str | None = None
    urgency: str | None = None
    lead_score: float = Field(ge=0.0, le=1.0)
    source: str = "chatbot"


class LeadQualifier:
    def update_from_message(self, session, message: str, service_interest: str | None = None, lead_score: float = 0.0) -> None:
        text = message.strip()
        lower = text.lower()

        name = self.extract_name(text, allow_short=not session.customer_name)
        if name and not session.customer_name:
            session.customer_name = name

        email = self.extract_email(text)
        if email:
            session.email = email

        if service_interest:
            session.service_interest = service_interest
        elif "botox" in lower:
            session.service_interest = "Botox"
        elif "filler" in lower:
            session.service_interest = "Fillers"
        elif "consult" in lower:
            session.service_interest = "Consultations"

        if "whatsapp" in lower:
            session.booking_preference = "WhatsApp"
        elif "website" in lower:
            session.booking_preference = "Website"

        if "this week" in lower:
            session.urgency = "This week"
        elif "today" in lower:
            session.urgency = "Today"
        elif "tomorrow" in lower:
            session.urgency = "Tomorrow"

        session.lead_score = max(session.lead_score, lead_score)

    def next_question(self, session) -> str | None:
        if not session.customer_name:
            return "May I take your name so the clinic team can address you properly?"
        if session.lead_score > 0.6 and not session.email:
            return "Could you share your email so the team can follow up?"
        if session.email and session.lead_score > 0.6 and not session.booking_preference:
            return "Would you prefer booking through WhatsApp or the website?"
        if session.email and session.lead_score > 0.6 and not session.urgency:
            return "When are you hoping to come in?"
        return None

    def build_lead(self, session) -> Lead | None:
        if not session.customer_name or not session.email:
            return None
        return Lead(
            name=session.customer_name,
            email=session.email,
            service_interest=session.service_interest,
            booking_preference=session.booking_preference,
            urgency=session.urgency,
            lead_score=session.lead_score,
        )

    @staticmethod
    def extract_email(text: str) -> str | None:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    @staticmethod
    def extract_name(text: str, allow_short: bool = False) -> str | None:
        patterns = [
            r"\bmy name is ([A-Za-z][A-Za-z\s'-]{1,40})",
            r"\bi am ([A-Za-z][A-Za-z\s'-]{1,40})",
            r"\bi'm ([A-Za-z][A-Za-z\s'-]{1,40})",
            r"\bim ([A-Za-z][A-Za-z\s'-]{1,40})",
            r"\bcall me ([A-Za-z][A-Za-z\s'-]{1,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                name = LeadQualifier._clean_name(match.group(1))
                return name if LeadQualifier._looks_like_name(name) else None

        if allow_short and re.fullmatch(r"[A-Za-z][A-Za-z\s'-]{1,30}", text.strip()):
            lower = text.lower()
            if not any(word in lower for word in ["price", "prices", "book", "botox", "filler", "consult", "aftercare", "hours"]):
                name = LeadQualifier._clean_name(text)
                return name if LeadQualifier._looks_like_name(name) else None
        return None

    @staticmethod
    def is_lead_detail_only(message: str) -> bool:
        lower = message.lower().strip()
        if LeadQualifier.extract_email(message):
            return True
        if lower in {"whatsapp", "website", "today", "tomorrow", "this week"}:
            return True
        blocked_words = {
            "price",
            "prices",
            "cost",
            "much",
            "book",
            "booking",
            "appointment",
            "botox",
            "filler",
            "fillers",
            "consult",
            "consultation",
            "consultations",
            "aftercare",
            "hours",
            "services",
            "service",
            "offered",
            "offer",
        }
        words = set(re.findall(r"[a-z]+", lower))
        if re.fullmatch(r"[A-Za-z][A-Za-z\s'-]{1,30}", message.strip()) and not words & blocked_words:
            return True
        return False

    @staticmethod
    def _clean_name(value: str) -> str:
        value = re.split(r"[.,!?]", value.strip())[0]
        stop_words = [" and ", " want ", " need ", " looking ", " interested "]
        for stop in stop_words:
            if stop in value.lower():
                value = value[: value.lower().index(stop)].strip()
        return " ".join(part.capitalize() for part in value.split())

    @staticmethod
    def _looks_like_name(value: str) -> bool:
        lower = value.lower()
        blocked = [
            "angry",
            "frustrated",
            "furious",
            "annoyed",
            "really",
            "very",
            "unhappy",
            "looking",
            "interested",
        ]
        return bool(value) and not any(word in lower.split() for word in blocked)
