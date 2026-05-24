ESCALATION_PROMPT = """
Check whether the latest customer message triggers escalation.

Escalate for:
- complaint
- medical question
- pricing negotiation
- more than 2 unanswered questions
- angry/frustrated sentiment
- explicit request for human agent
- out-of-scope question

Return JSON with:
should_escalate, reason, severity.
Severity must be low, medium, or high.
"""
