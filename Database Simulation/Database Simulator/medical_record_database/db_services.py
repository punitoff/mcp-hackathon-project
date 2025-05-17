import os, json
import random

base_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(base_dir, "synthea_sample_data_fhir_latest")

# Keep track of available and used patient files
_available_patient_files = []
_used_patient_files = set()

def _initialize_patient_files():
    """Initialize the list of available patient files if empty"""
    global _available_patient_files
    if not _available_patient_files:
        _available_patient_files = [f for f in os.listdir(database_path) if f.endswith('.json')]

def get_random_patient_record():
    """
    Returns a random patient record from the database without duplicates.
    Returns None if all patients have been used.
    """
    _initialize_patient_files()
    
    if not _available_patient_files:
        return None
        
    # Select and remove a random file from available files
    random_file = random.choice(_available_patient_files)
    _available_patient_files.remove(random_file)
    _used_patient_files.add(random_file)
    
    # Read and return the patient data
    file_path = os.path.join(database_path, random_file)
    with open(file_path) as f:
        data = json.load(f)
        print(data["entry"][0]["resource"]["id"])
        return {"id": data["entry"][0]["resource"]["id"], "data": data}

def reset_patient_selection():
    """Reset the patient selection, making all patients available again"""
    global _available_patient_files, _used_patient_files
    _available_patient_files = list(_available_patient_files + list(_used_patient_files))
    _used_patient_files.clear()