import json
import uuid
from datetime import datetime, timedelta, timezone
import random
import os
import glob

game_ids = [
    "apple_picking",
    "soccer",
    "skate",
    "flying",
    "gardening",
    "berry_picking",
    "hot_potato",
    "tomato_dodge",
    "rowing",
    "boxing"
]

def random_date_within_last_year():
    now = datetime.now(timezone.utc)
    delta_days = random.randint(0, 365)
    random_date = now - timedelta(days=delta_days)
    return random_date

def save_record_to_file(record, output_dir="database/records"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{record['id']}.json")
    with open(file_path, "w") as f:
        json.dump(record, f, indent=2)
    print(f"Saved record to {file_path}")

def process_synthea_records(synthea_dir, output_dir):
    # Validate synthea directory exists
    if not os.path.isdir(synthea_dir):
        raise ValueError(f"Synthea directory '{synthea_dir}' does not exist")

    os.makedirs(output_dir, exist_ok=True)
    
    # Get all patient JSON files from Synthea directory
    patient_files = glob.glob(os.path.join(synthea_dir, "*.json"))
    
    for patient_file in patient_files:
        with open(patient_file, 'r') as f:
            patient_data = json.load(f)
            
        # Extract patient ID from the Synthea record
        if isinstance(patient_data, dict) and "id" in patient_data["entry"][0]["resource"]:
            patient_id = patient_data["entry"][0]["resource"]["id"]
        else:
            # Skip if patient ID cannot be found
            print(f"Patient ID not found in {patient_file}")
            break
            
        # Generate and save Movemend record
        record = generate_patient_record(patient_id)
        save_record_to_file(record, output_dir)

def generate_patient_record(patient_id):
    record = {
        "resourceType": "MovemendRecord",
        "id": patient_id,
        "sessions": []
    }

    def generate_session(game_id):
        date = random_date_within_last_year()
        return {
            "gameId": game_id,
            "date": date.isoformat() + "Z",
            "score": random.randint(10, 25),
            "duration_minutes": random.randint(1, 10), # minutes
            "quality": random.randint(25, 100), #percent
            "notes": ""
        }
    
    game_session = random.randint(0, 10)
    for i in range(game_session):
        record["sessions"].append(generate_session(game_ids[random.randint(0, len(game_ids) - 1)]))

    return record


if __name__ == "__main__":
    synthea_dir = "../medical_record_database/synthea_sample_data_fhir_latest"
    output_dir = "movemend_patient_records"
    
    process_synthea_records(synthea_dir, output_dir)