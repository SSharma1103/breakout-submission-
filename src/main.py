from __future__ import annotations

import argparse
import json
import sys

from config import load_sop, use_openai
from memory.session_store import SessionStore
from workflow.conversation import CustomerSupportWorkflow


SCENARIOS = {
    "in_sop": ["What are your Botox prices?"],
    "out_of_scope": ["What aftercare should I follow after Botox?"],
    "escalation": ["I am really frustrated and want to complain about my appointment."],
    "lead": [
        "Hi, I'm Riya. I want Botox this week. Can I book on WhatsApp?",
        "riya@example.com",
    ],
    "summary": [
        "My name is Riya. What are your Botox prices?",
        "I want to book on WhatsApp this week.",
        "riya@example.com",
        "Am I medically eligible if I have allergies?",
    ],
}


def run_scenario(name: str) -> None:
    workflow = CustomerSupportWorkflow(load_sop())
    session = SessionStore().create()
    print(f"AI: {workflow.start_message(session)}")

    for customer_message in SCENARIOS[name]:
        print(f"Customer: {customer_message}")
        response = workflow.process_user_message(session, customer_message)
        print(f"AI: {response.message}")

    summary = workflow.final_summary(session)
    print("\nFinal structured summary:")
    print(json.dumps(summary.model_dump(), indent=2, ensure_ascii=False))


def run_interactive() -> None:
    workflow = CustomerSupportWorkflow(load_sop())
    session = SessionStore().create()
    print(f"AI: {workflow.start_message(session)}")
    if not use_openai():
        print("System: OPENAI_API_KEY is not set, so deterministic local fallbacks are being used.")

    while True:
        user_message = input("You: ").strip()
        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit", "summary"}:
            summary = workflow.final_summary(session)
            print("\nFinal structured summary:")
            print(json.dumps(summary.model_dump(), indent=2, ensure_ascii=False))
            break

        response = workflow.process_user_message(session, user_message)
        print(f"AI: {response.message}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Bloom Aesthetics Clinic AI support agent")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), help="Run a predefined demo scenario")
    args = parser.parse_args()

    if args.scenario:
        run_scenario(args.scenario)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
