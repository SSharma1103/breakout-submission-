# Closira AI Agent
video explanation (https://drive.google.com/file/d/1-zTIciGrf668ak97t6FYLNYRIADzGVG7/view)

Python CLI project for an AI customer support workflow for the fictional Bloom Aesthetics Clinic.

The agent handles four stages:

1. FAQ answering from SOP only
2. Lead qualification
3. Escalation detection
4. Conversation summary

If a customer asks something not present in the SOP, the agent does not guess. It escalates and logs the reason.

## Architecture

```text
CLI
  |
  v
SessionStore (in-memory state)
  |
  v
CustomerSupportWorkflow
  |
  +--> EscalationDetector      runs first on every user message
  +--> IntentClassifier        separates intent_confidence from lead_score
  +--> FAQAnswerer             answers only from data/sop.json
  +--> LeadQualifier           collects name, email, interest, preference, urgency
  +--> SummaryGenerator        produces final structured summary
  |
  v
MockDB
  +--> leads.json
  +--> conversations.json
  +--> escalations.jsonl
```

## Setup

```bash
cd closira-ai-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your OpenAI API key to `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

If no API key is present, the CLI still runs deterministic local fallbacks so the workflow can be demoed.

## Run

Interactive chat:

```bash
python src/main.py
```

End the session with:

```text
exit
quit
summary
```

The agent then prints a structured final summary and stores the conversation in `src/db/conversations.json`.

## Run Scenarios

```bash
python src/main.py --scenario in_sop
python src/main.py --scenario out_of_scope
python src/main.py --scenario escalation
python src/main.py --scenario lead
python src/main.py --scenario summary
```

## Folder Structure

```text
closira-ai-agent/
  README.md
  prompt_design.md
  requirements.txt
  .env.example
  data/
    sop.json
  src/
    main.py
    config.py
    workflow/
      conversation.py
      faq_answering.py
      intent_classifier.py
      lead_qualification.py
      escalation.py
      summary.py
    prompts/
      system_prompt.py
      summary_prompt.py
      escalation_prompt.py
    memory/
      session_store.py
    db/
      mock_db.py
      leads.json
      conversations.json
      escalations.jsonl
  test_transcripts/
    1_in_sop_question.md
    2_out_of_scope.md
    3_escalation_trigger.md
    4_lead_qualification.md
    5_conversation_summary.md
```

## Trade-offs and Limitations

- JSON files are used as a mock database, so this is not concurrency-safe.
- The local fallback logic is intentionally simple and exists only for demos without an API key.
- Real clinics would need stronger compliance review, richer SOPs, identity handling, audit trails, and secure storage.
- The SOP does not include appointment availability, aftercare, eligibility, discounts, or medical guidance, so those requests are escalated.
