# 5. Conversation Summary

AI: Hi, welcome to Bloom Aesthetics Clinic. I can help with SOP-backed questions about services, pricing, booking, and cancellation. May I take your name?

Customer: My name is Riya. What are your Botox prices?

AI: Botox starts from £200. Could you share your email so the team can follow up?

Customer: I want to book on WhatsApp this week.

AI: Bookings are available via WhatsApp or the website. Could you share your email so the team can follow up?

Customer: riya@example.com

AI: Thanks, I've saved your details for the clinic team to follow up.

Customer: Am I medically eligible if I have allergies?

AI: I don't have that information in the clinic SOP, so I'll pass this to a human team member.

Final summary:

```json
{
  "customer_intent": "Customer wanted Botox pricing or booking information",
  "key_details_collected": {
    "name": "Riya",
    "email": "riya@example.com",
    "service_interest": "Botox",
    "booking_preference": "WhatsApp",
    "urgency": "This week"
  },
  "sop_gaps_identified": [
    "SOP does not include medical eligibility or aftercare information"
  ],
  "recommended_next_action": "Human agent should review the escalation and follow up with the customer."
}
```
