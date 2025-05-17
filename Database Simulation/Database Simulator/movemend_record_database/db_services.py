import os, json
import random
import os.path

base_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(base_dir, "movemend_patient_records")

def get_from_patient_id(patient_id: str):
    path = f"{database_path}/{patient_id}.json"
    if not os.path.exists(path):
        print(f"Patient record not found for {patient_id}")
        return None
    with open(path) as f:
        return json.load(f)

