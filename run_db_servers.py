import subprocess
import sys
import os

def start_servers():
    # Get the path to the current Python interpreter
    python_executable = sys.executable
    print(f"Using Python interpreter: {python_executable}")
    
    # Define the paths to the servers
    db_sim_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Database Simulation', 'Database Simulator')
    
    # Change to the Database Simulator directory
    os.chdir(db_sim_dir)
    
    # Start the medical records server
    db_medical_records = subprocess.Popen([
        python_executable, "-m", "uvicorn", "medical_record_database.app:app", "--port", "8001"
    ])
    
    # Start the Movemend records server
    db_other = subprocess.Popen([
        python_executable, "-m", "uvicorn", "movemend_record_database.app:app", "--port", "8002"
    ])
    
    print("Servers started successfully!")
    print("Medical Records server running at: http://127.0.0.1:8001")
    print("Movemend Records server running at: http://127.0.0.1:8002")
    
    try:
        # Keep the servers running until keyboard interrupt
        db_medical_records.wait()
        db_other.wait()
    except KeyboardInterrupt:
        print("Shutting down servers...")
        db_medical_records.terminate()
        db_other.terminate()

if __name__ == "__main__":
    start_servers()
