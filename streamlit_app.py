"""
Streamlit Cloud entry point for the Clinical Copilot Dashboard.
This file redirects to the dashboard/clinical_copilot.py application.
"""
import streamlit as st
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import and run the dashboard application
sys.path.append(os.path.join(project_root, 'dashboard'))
from dashboard.clinical_copilot import main

# Run the main function from the dashboard
if __name__ == "__main__":
    main()
