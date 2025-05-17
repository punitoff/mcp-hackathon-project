from fastapi import FastAPI, HTTPException
from movemend_record_database.db_services import get_from_patient_id

app = FastAPI()

@app.get("/db_id")
def ping():
    return {"db_id": "movemend_database"}

@app.get("/patient_dossier/{patient_id}")
def read_patient_dossier(patient_id: str):
    return get_from_patient_id(patient_id)

