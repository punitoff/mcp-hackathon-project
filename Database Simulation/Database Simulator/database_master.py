import subprocess

def start_servers():
    db_medical_records = subprocess.Popen([
        "python3", "-m", "uvicorn", "medical_record_database.app:app", "--port", "8001"
    ])
    db_other = subprocess.Popen([
        "python3", "-m", "uvicorn", "movemend_record_database.app:app", "--port", "8002"
    ])

    print("Servers started.")
    try:
        db_medical_records.wait()
        db_other.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        db_medical_records.terminate()
        db_other.terminate()


if __name__ == "__main__":
    start_servers()