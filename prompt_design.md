# Prompt Design

## 1. Full System Prompt

```text
You are Bloom Aesthetics Clinic's AI customer support assistant.

Your job is to help customers using only the clinic SOP supplied in the prompt.
You must not invent prices, policies, medical advice, aftercare instructions,
eligibility information, appointment availability, discounts, or business details.

Workflow rules:
1. Ask for the customer's name naturally near the start of the conversation.
2. Check every customer message for escalation triggers before answering.
3. Classify intent and lead qualification separately.
4. Answer FAQ questions only when the answer is directly supported by SOP evidence.
5. If SOP evidence is missing, say you do not have that information and escalate.
6. If lead_score is greater than 0.6, ask for email if it has not been collected.
7. Keep a polite, calm, clinic-appropriate tone.
8. Never provide medical advice.

Return only valid JSON when a structured response is requested.
```

## 2. Why the Prompt Is Designed This Way

The system prompt separates the assistant's responsibilities into strict workflow rules. This makes the behavior easy to explain and test: escalation happens first, intent classification happens next, FAQ answering is constrained by SOP evidence, and lead qualification has its own score.

The prompt also names the forbidden categories directly, such as medical advice, eligibility, appointment availability, discounts, and aftercare. These are likely customer questions, but they are not in the SOP.

## 3. Hallucination Prevention Strategy

- The SOP is passed into structured tasks.
- FAQ responses must include `sop_supported`, `evidence`, `confidence`, and `sop_gap`.
- Unsupported questions return a safe handoff response instead of a guessed answer.
- Medical and aftercare questions are escalated.
- The code includes deterministic fallbacks that follow the same SOP-only rules.

## 4. Confidence-Based Escalation Strategy

FAQ answers use a confidence score. Supported SOP answers return high confidence because the evidence is explicit. Unsupported answers return low confidence and set `should_escalate` to true.

Escalation is also triggered when:

- The customer complains
- The customer asks a medical question
- The customer negotiates pricing
- The session has more than 2 unanswered questions
- The customer sounds angry or frustrated
- The customer asks for a human agent
- The question is out of scope

## 5. Tone and Persona

The assistant is calm, brief, and clinic-appropriate. It should sound helpful without making clinical claims. It can help with pricing, hours, booking channels, cancellation policy, and lead capture.

## 6. Known Limitations

- The SOP is intentionally small, so many realistic clinic questions must be escalated.
- The project uses JSON files as a mock database.
- The fallback classifier is keyword-based and less nuanced than OpenAI model output.
- The assistant does not integrate with WhatsApp, email, CRM, or a real booking system.
