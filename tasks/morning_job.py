"""Sample morning summary job runnable via `python -m tasks.morning_job`."""
import os
from summarization.generate import main as run_summary


def job():
    patient_id = os.getenv("PATIENT_ID", "patient-1")
    run_summary(patient_id)


if __name__ == "__main__":
    job()
