from fastapi import FastAPI, HTTPException
from medical_record_database.db_services import get_random_patient_record

app = FastAPI()

@app.get("/db_id")
def ping():
    return {"db_id": "synthea_database"}

@app.get("/random_patient_list/{count}")
def read_random_patient_records(count: int):
    records = []
    print(f"Getting {count} random patient records")
    
    for _ in range(count):
        record = get_random_patient_record()
        if record:
            records.append(record)
        

    return records
    
