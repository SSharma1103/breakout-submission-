# 2. Out-of-Scope

AI: Hi, welcome to Bloom Aesthetics Clinic. I can help with SOP-backed questions about services, pricing, booking, and cancellation. May I take your name?

Customer: What aftercare should I follow after Botox?

AI: I don't have that information in the clinic SOP, so I'll pass this to a human team member.

Escalation JSON shape:

```json
{
  "should_escalate": true,
  "reason": "Customer asked a medical or aftercare question",
  "severity": "high"
}
```
