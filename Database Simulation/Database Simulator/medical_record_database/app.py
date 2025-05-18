from fastapi import FastAPI, HTTPException
from medical_record_database.db_services import get_random_patient_record, reset_patient_selection, _available_patient_files

app = FastAPI()

@app.get("/db_id")
def ping():
    return {"db_id": "synthea_database"}

@app.get("/random_patient_list/{count}")
def read_random_patient_records(count: int):
    records = []
    # First check if we have enough patients available
    if len(_available_patient_files) < count:
        # Reset the patient selection if we don't have enough patients
        reset_patient_selection()
        print(f"Reset patient selection to fulfill request for {count} patients")
    
    # Now get the requested number of patients
    for i in range(count):
        record = get_random_patient_record()
        if record:
            records.append(record)
        else:
            # If we still can't get enough patients, reset again
            reset_patient_selection()
            record = get_random_patient_record()
            if record:
                records.append(record)
    
    print(f"Returning {len(records)} patient records")
    return records
