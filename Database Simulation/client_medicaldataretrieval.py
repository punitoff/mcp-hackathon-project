import requests

def ping_dbs():
    base_url = "http://127.0.0.1:8001"
    endpoint = f"/db_id"
    try:
        response = requests.get(base_url + endpoint)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving database id: {e}")
        return []
    
    base_url_2 = "http://127.0.0.1:8002"
    endpoint = f"/db_id"
    try:
        response = requests.get(base_url_2 + endpoint)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving database id: {e}")
        return []

def get_random_patient_data(count: int):

    base_url = "http://127.0.0.1:8001"
    endpoint = f"/random_patient_list/{count}"
    try:
        records = requests.get(base_url + endpoint)
        records.raise_for_status()  # Raises HTTPError for 4xx/5xx
        return records
    
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving patient list: {e}")
        return []
    
def get_movemend_data(patient_id: str):
    base_url = "http://127.0.0.1:8002"
    endpoint = f"/patient_dossier/{patient_id}"
    try:
        records = requests.get(base_url + endpoint)
        records.raise_for_status()  # Raises HTTPError for 4xx/5xx
        return records  
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving movemend data: {e}")
        return []

if __name__ == "__main__":
    ping_dbs()
    records = get_random_patient_data(25)
    records_json = records.json()
    for record in records_json:
        print(record["id"])
        record["movemend_data"] = get_movemend_data(record["id"]).json()
        print("linked movemend data")
        print("sessions: ", len(record["movemend_data"]["sessions"]))
