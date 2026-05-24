from __future__ import annotations

from pydantic import BaseModel

from db.mock_db import MockDB
from memory.session_store import SessionState
from workflow.escalation import EscalationDetector
from workflow.faq_answering import FAQAnswerer
from workflow.intent_classifier import IntentClassifier
from workflow.lead_qualification import LeadQualifier
from workflow.summary import ConversationSummary, SummaryGenerator


class AgentResponse(BaseModel):
    message: str
    escalated: bool = False
    saved_lead: bool = False


class CustomerSupportWorkflow:
    def __init__(self, sop: dict, db: MockDB | None = None) -> None:
        self.sop = sop
        self.db = db or MockDB()
        self.escalation_detector = EscalationDetector(sop)
        self.intent_classifier = IntentClassifier(sop)
        self.faq_answerer = FAQAnswerer(sop)
        self.lead_qualifier = LeadQualifier()
        self.summary_generator = SummaryGenerator(sop)

    def start_message(self, session: SessionState) -> str:
        message = (
            "Hi, welcome to Bloom Aesthetics Clinic. "
            "I can help with SOP-backed questions about services, pricing, booking, and cancellation. "
            "May I take your name?"
        )
        session.add_message("assistant", message)
        return message

    def process_user_message(self, session: SessionState, message: str) -> AgentResponse:
        session.add_message("user", message)

        escalation = self.escalation_detector.detect(message, session.unanswered_count)
        if escalation.should_escalate:
            reply = self._handle_escalation(session, message, escalation.reason, escalation.severity)
            return AgentResponse(message=reply, escalated=True)

        intent = self.intent_classifier.classify(message)
        session.intent_confidence = intent.intent_confidence
        self.lead_qualifier.update_from_message(
            session,
            message,
            service_interest=intent.service_interest,
            lead_score=intent.lead_score,
        )

        if self.lead_qualifier.is_lead_detail_only(message):
            reply = self._lead_follow_up(session)
            session.add_message("assistant", reply)
            return AgentResponse(message=reply, saved_lead=session.lead_saved)

        answer = self.faq_answerer.answer(message)
        reply_parts = [answer.answer]

        if answer.should_escalate:
            session.unanswered_count += 1
            if answer.sop_gap and answer.sop_gap not in session.sop_gaps:
                session.sop_gaps.append(answer.sop_gap)
            self._log_escalation(
                session,
                reason=answer.escalation_reason or "Out-of-scope question",
                severity="medium",
                user_message=message,
            )
            if session.unanswered_count > 2:
                self._log_escalation(
                    session,
                    reason="More than 2 unanswered SOP questions",
                    severity="medium",
                    user_message=message,
                )
            reply = " ".join(reply_parts)
            session.add_message("assistant", reply)
            return AgentResponse(message=reply, escalated=True)

        next_question = self.lead_qualifier.next_question(session)
        if next_question:
            reply_parts.append(next_question)

        reply = " ".join(reply_parts)
        session.add_message("assistant", reply)
        return AgentResponse(message=reply)

    def final_summary(self, session: SessionState) -> ConversationSummary:
        summary = self.summary_generator.generate(session)
        self.db.save_conversation(
            {
                "session_id": session.session_id,
                "messages": session.transcript(),
                "summary": summary.model_dump(),
            }
        )
        return summary

    def _lead_follow_up(self, session: SessionState) -> str:
        lead = self.lead_qualifier.build_lead(session)
        if lead and not session.lead_saved:
            self.db.save_lead(lead.model_dump())
            session.lead_saved = True

        next_question = self.lead_qualifier.next_question(session)
        if next_question:
            if session.customer_name:
                return f"Thanks, {session.customer_name}. {next_question}"
            return next_question

        if session.lead_saved:
            return "Thanks, I've saved your details for the clinic team to follow up."
        return "Thanks. How can I help with Bloom Aesthetics Clinic today?"

    def _handle_escalation(self, session: SessionState, user_message: str, reason: str | None, severity: str) -> str:
        reason = reason or "Escalation trigger detected"
        self._log_escalation(session, reason=reason, severity=severity, user_message=user_message)
        lower_reason = reason.lower()
        lower_message = user_message.lower()
        if "medical" in lower_reason or "aftercare" in lower_message:
            gap = "SOP does not include medical eligibility or aftercare information"
            if gap not in session.sop_gaps:
                session.sop_gaps.append(gap)
            reply = (
                "I don't have that information in the clinic SOP, so I'll pass this "
                "to a human team member."
            )
        else:
            reply = "I understand. I'll pass this to a human team member so they can help properly."
        session.add_message("assistant", reply)
        return reply

    def _log_escalation(self, session: SessionState, reason: str, severity: str, user_message: str) -> None:
        session.escalation_reasons.append(reason)
        self.db.log_escalation(
            {
                "session_id": session.session_id,
                "reason": reason,
                "severity": severity,
                "user_message": user_message,
            }
        )
