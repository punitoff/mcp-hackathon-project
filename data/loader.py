"""Simple utilities to load synthetic FHIR JSON bundles."""
from pathlib import Path
import json
from typing import Dict, Any

DATA_DIR = Path(__file__).resolve().parent / "patients"


def load_patient_bundle(patient_id: str) -> Dict[str, Any]:
    """Return the full FHIR bundle for a given synthetic patient ID.

    Assumes files are stored as <patient_id>.json under data/patients.
    """
    bundle_path = DATA_DIR / f"{patient_id}.json"
    if not bundle_path.exists():
        raise FileNotFoundError(f"Patient bundle not found: {bundle_path}")

    with open(bundle_path, "r", encoding="utf-8") as f:
        return json.load(f)
