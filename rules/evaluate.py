"""Evaluate basic alert rules on a FHIR bundle."""
from typing import Any, Dict, List


def evaluate_rules(bundle: Dict[str, Any]) -> List[str]:
    """Return list of alert strings."""
    alerts: List[str] = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {}).get("text", "")
            if code.lower().startswith("blood pressure"):
                systolic = _extract_quantity(resource)
                if systolic and systolic < 90:
                    alerts.append("Low blood pressure < 90 mmHg")
            if code.lower().startswith("oxygen saturation"):
                sat = _extract_quantity(resource)
                if sat and sat < 90:
                    alerts.append("Low O2 saturation < 90%")

    return alerts


def _extract_quantity(obs: Dict[str, Any]):
    for component in [obs] + obs.get("component", []):
        if "valueQuantity" in component:
            return component["valueQuantity"].get("value")
    return None
