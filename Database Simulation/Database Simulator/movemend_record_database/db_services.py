import os, json
import random
import os.path
import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(base_dir, "movemend_patient_records")

def get_from_patient_id(patient_id: str):
    path = f"{database_path}/{patient_id}.json"
    if not os.path.exists(path):
        print(f"Patient record not found for {patient_id}, generating simulated data")
        # Generate simulated Movemend data using patient ID as seed
        return generate_movemend_data(patient_id)
    with open(path) as f:
        return json.load(f)

def generate_movemend_data(patient_id: str):
    """Generate simulated Movemend data for patients without records"""
    # Use the patient ID as a seed for consistent random generation
    random.seed(hash(patient_id))
    
    # Generate exercise data
    exercise_types = ["gardening", "boxing", "rowing", "soccer", "berry_picking", 
                    "hot_potato", "fishing", "dancing", "bowling", "tennis"]
    
    # Create 3-8 sessions
    num_sessions = random.randint(3, 8)
    sessions = []
    
    # Get current date for reference
    today = datetime.datetime.now()
    
    for _ in range(num_sessions):
        # Random date in past year
        days_ago = random.randint(0, 365)
        session_date = today - datetime.timedelta(days=days_ago)
        
        # Create session data
        sessions.append({
            "gameId": random.choice(exercise_types),
            "date": session_date.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00Z"),
            "score": random.randint(5, 25),
            "duration_minutes": random.randint(1, 10),
            "quality": random.randint(30, 95),
            "notes": ""
        })
    
    # Sort by date (newest first)
    sessions.sort(key=lambda x: x["date"], reverse=True)
    
    # Provider names
    provider_names = ["Dr. Sarah Johnson", "Dr. Robert Chen", "Dr. Maria Rodriguez", 
                    "Dr. James Wilson", "Dr. Emily Thompson", "Dr. Michael Brown"]
    random.shuffle(provider_names)
    
    # Create complete record
    record = {
        "resourceType": "MovemendRecord",
        "id": patient_id,
        "sessions": sessions,
        "primary_provider": provider_names[0],
        "specialist": provider_names[1],
        "last_visit_date": (today - datetime.timedelta(days=random.randint(5, 60))).strftime("%Y-%m-%d"),
        "next_appointment": (today + datetime.timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d"),
        "notes": []
    }
    
    # Reset random seed
    random.seed()
    
    return record

