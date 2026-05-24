SUMMARY_PROMPT = """
Create a structured conversation summary for a human clinic team member.

Include:
- customer_intent
- key_details_collected
- sop_gaps_identified
- recommended_next_action

Use only facts from the conversation state and SOP gap log.
Return valid JSON only.
"""
