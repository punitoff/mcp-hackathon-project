"""Entry point for generating morning summary & alerts for a patient."""
import asyncio
from typing import Dict, Any

from data.loader import load_patient_bundle
from llm.openai_client import chat_async
from rules.evaluate import evaluate_rules


SUMMARY_PROMPT_SYSTEM = """You are an expert physical therapy assistant. Generate a concise clinician-facing summary and an alert section."""


async def generate_summary_and_alerts(patient_id: str) -> Dict[str, Any]:
    bundle = load_patient_bundle(patient_id)
    alerts = evaluate_rules(bundle)

    messages = [
        {"role": "system", "content": SUMMARY_PROMPT_SYSTEM},
        {
            "role": "user",
            "content": f"""Here is the patient's FHIR bundle JSON:\n\n{bundle}\n\nHard-coded alerts: {alerts}. Please generate:\n1. Morning Summary (focus on latest changes)\n2. Alerts (critical issues, trends)""",
        },
    ]

    llm_response = await chat_async(messages)
    return {
        "alerts": alerts,
        "llm_output": llm_response["message"]["content"],
    }


def main(patient_id: str):
    result = asyncio.run(generate_summary_and_alerts(patient_id))
    print(result["llm_output"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m summarization.generate <patient_id>")
        sys.exit(1)

    main(sys.argv[1])
