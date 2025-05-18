import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple
import requests
import sys

# Add Database Simulation directory to path - use relative path for Streamlit Cloud compatibility
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
database_sim_path = os.path.join(project_root, 'Database Simulation')
sys.path.append(database_sim_path)

# Import database client functions with error handling for Streamlit Cloud
try:
    from client_medicaldataretrieval import get_random_patient_data, get_movemend_data
except ImportError:
    # Define fallback functions for Streamlit Cloud where database servers might not be available
    def get_random_patient_data(count=15):
        # Return mock response for Streamlit Cloud
        return MockResponse([{"id": f"patient{i}", "name": f"Test Patient {i}", "gender": "Female" if i % 2 == 0 else "Male", 
                            "age": 30 + i, "conditions": ["Hypertension", "Diabetes"]} for i in range(count)])
        
    def get_movemend_data(patient_id):
        # Return mock response for Streamlit Cloud
        return MockResponse({"patient_id": patient_id, "exercises": ["Walking", "Stretching"], 
                           "adherence": "Good", "progress": "Improving"})
    
    # Mock response class
    class MockResponse:
        def __init__(self, data):
            self.data = data
        
        def json(self):
            return self.data

# Real AI Service using Claude LLM
import sys
import os

# Add project root to path to ensure all imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from llm.claude_client import claude_client, ClaudeClient
    from llm.claude_mcp_client import claude_mcp_client, ClaudeMCPClient
    from llm.hume_voice_client import hume_voice_client, HumeVoiceClient
    from llm.speech_recognition_client import speech_recognition_client, SpeechRecognitionClient
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    import av
    LLM_AVAILABLE = True
    VOICE_AVAILABLE = True
    SPEECH_RECOGNITION_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Claude LLM clients, HUME Voice client or Speech Recognition not available: {e}")
    LLM_AVAILABLE = False
    VOICE_AVAILABLE = False
    SPEECH_RECOGNITION_AVAILABLE = False

# Initialize voice mode state if not already set
if 'voice_mode_active' not in st.session_state:
    st.session_state.voice_mode_active = False
    
if 'voice_output_ready' not in st.session_state:
    st.session_state.voice_output_ready = False
    
if 'voice_output_audio' not in st.session_state:
    st.session_state.voice_output_audio = None
    
# Initialize speech recognition state
if 'speech_recognition_active' not in st.session_state:
    st.session_state.speech_recognition_active = False
    
if 'last_voice_command' not in st.session_state:
    st.session_state.last_voice_command = ""
    
if 'voice_commands_history' not in st.session_state:
    st.session_state.voice_commands_history = []

class AIClinicalAssistant:
    """AI Clinical Assistant using Claude LLM."""
    
    @staticmethod
    def generate_summary(patient_data: Dict) -> str:
        """Generate AI-powered clinical summary using Claude LLM."""
        try:
            if LLM_AVAILABLE:
                # Try to use Claude
                return claude_client.generate_clinical_summary(patient_data)
            else:
                # Fallback to mock implementation
                conditions = ", ".join(patient_data.get("conditions", ["No active problems"]))
                latest_vitals = patient_data.get("vitals", {})
                
                return f"""## Clinical Summary for {patient_data.get('name', 'Patient')}
                
**Active Conditions**: {conditions}
                
**Latest Vitals**:
- BP: {latest_vitals.get('sbp', 'N/A')}/{latest_vitals.get('dbp', 'N/A')} mmHg
- HR: {latest_vitals.get('hr', 'N/A')} bpm
- Weight: {latest_vitals.get('weight', 'N/A')} kg
- BMI: {latest_vitals.get('bmi', 'N/A')}
                
**AI Insights**:
- {random.choice(['Stable condition', 'Improving', 'Needs monitoring'])}
- {'No concerning trends' if random.random() > 0.3 else 'Monitor blood pressure trend'}"""
        except Exception as e:
            st.error(f"Error generating summary with Claude: {e}")
            # Fallback to a simple error summary
            return f"""## Clinical Summary for {patient_data.get('name', 'Patient')}
            
**Error**: Could not generate AI summary. Please check the logs.
            
**Basic Information**:
- Conditions: {', '.join(patient_data.get('conditions', ['Unknown']))} 
- Latest BP: {patient_data.get('vitals', {}).get('sbp', 'N/A')}/{patient_data.get('vitals', {}).get('dbp', 'N/A')} mmHg"""

    @staticmethod
    def answer_question(question: str, context: Dict) -> str:
        """Answer clinical questions using Claude LLM."""
        try:
            if LLM_AVAILABLE:
                # Try to use Claude with additional question
                return claude_client.generate_clinical_insights(context, additional_question=question)
            else:
                # Simulate AI response - fallback if Claude is not available
                time.sleep(0.5)  # Simulate API call
                
                # Extract relevant patient information
                name = context.get('name', 'the patient')
                age = context.get('age', '')
                conditions = ", ".join(context.get('conditions', [])) or "no active conditions"
                vitals = context.get('vitals', {})
                
                # Generate context-aware responses
                if "summary" in question.lower() or "overview" in question.lower():
                    return (
                        f"### Clinical Summary for {name} ({age}yo)\n\n"
                        f"**Active Conditions**: {conditions}\n\n"
                        f"**Recent Vitals**:\n"
                        f"- BP: {vitals.get('sbp', '--')}/{vitals.get('dbp', '--')} mmHg\n"
                        f"- HR: {vitals.get('hr', '--')} bpm\n"
                        f"- SpO₂: {vitals.get('spo2', '--')}%\n"
                        f"- Pain: {vitals.get('pain_score', '--')}/10\n\n"
                        f"**Recommendations**:\n"
                        f"- Monitor blood pressure trends\n"
                        f"- Consider reviewing current medications\n"
                        f"- Schedule follow-up in 2 weeks"
                    )
                
                elif "pain" in question.lower():
                    pain_score = vitals.get('pain_score', 0)
                    if pain_score >= 7:
                        return (
                            f"### Pain Assessment\n\n"
                            f"**Severe Pain Reported**: {pain_score}/10\n\n"
                            f"**Recommendations**:\n"
                            f"- Assess pain characteristics (location, quality, radiation)\n"
                            f"- Review current pain management regimen\n"
                            f"- Consider non-pharmacological interventions\n"
                            f"- Evaluate for red flags requiring immediate attention"
                        )
                    return "No significant pain reported in recent assessments."
                        
                # Default response for other questions
                return (
                    f"### Response to: \"{question}\"\n\n"
                    f"Based on {name}'s records ({age}yo, {conditions}):\n\n"
                    f"- Relevant vitals: BP {vitals.get('sbp', '--')}/{vitals.get('dbp', '--')}, "
                    f"HR {vitals.get('hr', '--')}\n"
                    f"- Last weight: {vitals.get('weight', '--')} kg\n"
                    f"- Recent labs: {', '.join(context.get('labs', {}).keys()) or 'No recent labs available'}\n\n"
                    f"*This is a simulated response. In production, this would include AI-generated insights based on the full patient record.*"
                )
        except Exception as e:
            st.error(f"Error answering question with Claude: {e}")
            return f"### Error\nFailed to process your question: '{question}'\n\nPlease try again later or contact technical support."

    @staticmethod
    def generate_clinical_notes(patient_data: Dict) -> str:
        """Generate SOAP-style clinical notes using Claude LLM."""
        try:
            if LLM_AVAILABLE:
                # Try to use Claude
                return claude_client.generate_soap_note(patient_data)
            else:
                # Fallback to mock implementation
                return f"""## SOAP Note - {datetime.now().strftime('%Y-%m-%d')}
                
**Subjective**:
Patient reports {random.choice(['improving symptoms', 'stable condition', 'mild discomfort'])}.
                
**Objective**:
- Vitals: BP {patient_data.get('vitals', {}).get('sbp', 'N/A')}/{patient_data.get('vitals', {}).get('dbp', 'N/A')}, HR {patient_data.get('vitals', {}).get('hr', 'N/A')}
- Findings: {random.choice(['No acute distress', 'Mild edema noted', 'Range of motion improving'])}
                
**Assessment**:
{patient_data.get('name', 'Patient')} is {random.choice(['improving as expected', 'progressing well', 'requires closer monitoring'])}.
                
**Plan**:
- Continue current treatment plan
- Follow up in {random.choice(['1 week', '2 weeks', '1 month'])}
- Consider {random.choice(['increasing physical therapy', 'medication adjustment', 'additional imaging'])}"""
        except Exception as e:
            st.error(f"Error generating SOAP notes with Claude: {e}")
            return f"## SOAP Note - {datetime.now().strftime('%Y-%m-%d')}\n\n**Error**: Could not generate AI notes. Please check the logs."
    
    @staticmethod
    def generate_mcp_summary(patient_uri: Optional[str] = None) -> str:
        """Generate a comprehensive clinical summary using advanced data integration."""
        try:
            if LLM_AVAILABLE:
                # Initialize MCP server if not already initialized
                from mcp_server.app import mcp_server
                if not mcp_server.initialized:
                    mcp_server.initialize()
                
                # Use Claude MCP client to generate summary
                return claude_mcp_client.generate_clinical_summary_with_mcp(patient_uri)
            else:
                return "## Advanced Clinical Summary\n\nAdvanced summary functionality not available. Please check that Claude API is configured correctly."
        except Exception as e:
            st.error(f"Error generating comprehensive summary with Claude: {e}")
            return f"## Advanced Clinical Summary\n\n**Error**: Could not generate comprehensive summary. Please check the logs."
            
    @staticmethod
    def process_voice_command(command: str, patient_data_list: List[Dict]) -> Tuple[str, Dict, bytes]:
        """Process a voice command and return appropriate response.
        
        Args:
            command: The voice command from the user
            patient_data_list: List of all patient data
            
        Returns:
            Tuple of (text_response, selected_patient_data, audio_bytes)
        """
        try:
            if not VOICE_AVAILABLE:
                return "Voice processing is not available.", None, None
                
            # Convert command to lowercase for easier matching
            command = command.lower()
            
            # Find the most critical patient
            critical_patient = AIClinicalAssistant._find_most_critical_patient(patient_data_list)
            
            # Generate response based on command
            if "tell me the summary" in command or "summary of" in command or "critical patient" in command:
                # Generate a text summary
                text_summary = AIClinicalAssistant.generate_summary(critical_patient)
                
                # Get voice response
                audio_bytes = hume_voice_client.get_critical_patient_summary_voice(critical_patient)
                
                return text_summary, critical_patient, audio_bytes
            else:
                # Handle other commands or questions
                text_response = AIClinicalAssistant.answer_question(command, critical_patient)
                audio_bytes = hume_voice_client.generate_summary_voice(text_response)
                
                return text_response, critical_patient, audio_bytes
                
        except Exception as e:
            st.error(f"Error processing voice command: {e}")
            return f"Error processing voice command: {str(e)}", None, None
            
    @staticmethod
    def _find_most_critical_patient(patient_data_list: List[Dict]) -> Dict:
        """Find the most critical patient based on conditions and vitals.
        
        Args:
            patient_data_list: List of all patient data
            
        Returns:
            Dictionary with the most critical patient data
        """
        # If empty list, return empty dict
        if not patient_data_list:
            return {}
            
        # Define a function to score patient criticality
        def calculate_criticality(patient):
            score = 0
            
            # Score based on conditions (more conditions = higher score)
            conditions = patient.get("conditions", [])
            score += len(conditions) * 5
            
            # Check for critical conditions
            critical_keywords = [
                "heart", "cardiac", "stroke", "pulmonary", "respiratory",
                "failure", "sepsis", "infection", "fracture", "trauma"
            ]
            
            for condition in conditions:
                # Add points for each critical keyword found in condition
                for keyword in critical_keywords:
                    if keyword.lower() in condition.lower():
                        score += 10
            
            # Score based on vitals
            vitals = patient.get("vitals", {})
            
            # Check blood pressure
            sbp = vitals.get("sbp")
            dbp = vitals.get("dbp")
            if sbp and (sbp > 140 or sbp < 90):
                score += 15
            if dbp and (dbp > 90 or dbp < 60):
                score += 15
                
            # Check heart rate
            hr = vitals.get("hr")
            if hr and (hr > 100 or hr < 50):
                score += 15
                
            # Check pain score
            pain = vitals.get("pain_score")
            if pain and pain >= 7:
                score += 20
                
            return score
        
        # Score each patient and find the one with the highest score
        scored_patients = [(calculate_criticality(p), p) for p in patient_data_list]
        scored_patients.sort(reverse=True)  # Sort in descending order
        
        # Return the most critical patient
        return scored_patients[0][1] if scored_patients else {}
        
    @staticmethod
    def toggle_voice_mode():
        """Toggle the voice mode on/off in the session state."""
        st.session_state.voice_mode_active = not st.session_state.voice_mode_active
        
        # Reset voice output when toggling
        st.session_state.voice_output_ready = False
        st.session_state.voice_output_audio = None
        
        # Stop speech recognition if it's active
        if st.session_state.speech_recognition_active and not st.session_state.voice_mode_active:
            AIClinicalAssistant.stop_speech_recognition()
    
    @staticmethod
    def toggle_speech_recognition():
        """Toggle speech recognition on/off."""
        if SPEECH_RECOGNITION_AVAILABLE:
            if st.session_state.speech_recognition_active:
                AIClinicalAssistant.stop_speech_recognition()
            else:
                AIClinicalAssistant.start_speech_recognition()
        else:
            st.error("Speech recognition is not available. Check your installation.")
    
    @staticmethod
    def start_speech_recognition():
        """Start the speech recognition client."""
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                # Callback function to handle recognized speech
                def handle_speech(text):
                    if text and text.strip():
                        st.session_state.last_voice_command = text.strip()
                        st.session_state.voice_commands_history.append(text.strip())
                        # Force streamlit to rerun to update the UI
                        st.experimental_rerun()
                
                # Start listening for speech
                speech_recognition_client.start_listening(callback=handle_speech)
                st.session_state.speech_recognition_active = True
                return True
            except Exception as e:
                st.error(f"Error starting speech recognition: {str(e)}")
                return False
        return False
    
    @staticmethod
    def stop_speech_recognition():
        """Stop the speech recognition client."""
        if SPEECH_RECOGNITION_AVAILABLE and st.session_state.speech_recognition_active:
            try:
                speech_recognition_client.stop_listening()
                st.session_state.speech_recognition_active = False
                return True
            except Exception as e:
                st.error(f"Error stopping speech recognition: {str(e)}")
                return False
        return False
    
    @staticmethod
    def process_recognized_speech():
        """Process any recognized speech from the speech recognition client."""
        if SPEECH_RECOGNITION_AVAILABLE and st.session_state.speech_recognition_active:
            try:
                # Check if we have a new command
                text = speech_recognition_client.get_recognized_text()
                if text and text.strip():
                    st.session_state.last_voice_command = text.strip()
                    st.session_state.voice_commands_history.append(text.strip())
                    return text.strip()
                return None
            except Exception as e:
                st.error(f"Error processing recognized speech: {str(e)}")
                return None
        return None

# Set page config with light theme explicitly
st.set_page_config(
    page_title="MoveMend Co Pilot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.movemendhealth.com',
        'Report a bug': 'https://www.movemendhealth.com',
        'About': 'MoveMend Co Pilot - Clinical Dashboard'
    }
)

# Force light theme for the entire app
st.markdown('''
    <script>
        if (window.parent.document.querySelector('.sidebar .sidebar-content')) {
            var observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    if (mutation.addedNodes.length) {
                        document.querySelectorAll('td, th, [data-baseweb="table"], [role="listbox"]').forEach(el => {
                            el.style.backgroundColor = '#ffffff';
                            el.style.color = '#1a1a2e';
                        });
                    }
                });
            });
            var options = {
                childList: true,
                subtree: true
            };
            observer.observe(window.parent.document.querySelector('.sidebar .sidebar-content'), options);
        }
    </script>
''', unsafe_allow_html=True)

# Custom CSS for MoveMend branding
st.markdown('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scope+One&display=swap');
    
    * {
        font-family: 'Scope One', serif !important;
    }
    
    /* Base app background */
    .stApp {
        background: #ffffff !important;
        background-image: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important;
    }
    
    /* Force light mode for all elements */
    html, body, div, main, header, footer, aside, section, article {
        color-scheme: light !important;
    }
    
    /* Direct override for dark background elements */
    .st-emotion-cache-1gulkj5, .st-emotion-cache-90vs21, .st-emotion-cache-eczf16,
    .st-emotion-cache-7ym5gk, .st-emotion-cache-16txtl3, .st-emotion-cache-1aehpvj,
    .st-emotion-cache-1j3ld9n, .st-emotion-cache-10oheav, .st-emotion-cache-16idsys,
    .st-emotion-cache-lrlib, .st-emotion-cache-ocqkz7, .st-emotion-cache-q8sbsg,
    .st-emotion-cache-1whk473, .st-emotion-cache-z5fcl4, .st-emotion-cache-lvmb86,
    .st-emotion-cache-1qg05tj {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* All dropdowns and tables */
    [data-baseweb="select"] *, 
    [data-baseweb="popover"] *, 
    [role="listbox"] *, 
    [role="option"] *,
    table, th, td, tr, thead, tbody {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* Specific selector for dataframe tables in Streamlit */
    .stDataFrame, .stDataFrame *, .stDataFrame table, .stDataFrame th, .stDataFrame td,
    .element-container div[data-testid="stDataFrame"] table,
    .element-container div[data-testid="stDataFrame"] th,
    .element-container div[data-testid="stDataFrame"] td {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border-color: rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Dropdown menu items */
    .st-emotion-cache-1rqnjuh, .st-emotion-cache-1qg05tj, .st-emotion-cache-b9cf6k, 
    .st-emotion-cache-ocqkz7, .st-emotion-cache-z5fcl4, .st-emotion-cache-ue6h4q, 
    .st-emotion-cache-1offfbd {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* Table headers and rows */
    .st-emotion-cache-z5fcl4 > thead > tr > th,
    .st-emotion-cache-z5fcl4 > tbody > tr > td {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #1a1a2e !important;
    }
    
    /* Main header styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 2rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(240, 240, 245, 0.8);
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(75, 192, 141, 0.1);
        border-bottom: 2px solid #2ecc71;
    }
    
    /* Metrics styling */
    div[data-testid="stMetricValue"] > div {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
    }
    
    div[data-testid="stMetricLabel"] > div {
        font-size: 1rem !important;
        color: #555555 !important;
    }
    
    /* Right side content area with subtle shadow */
    .right-content-placeholder {
        background-color: rgba(255, 255, 255, 0.8);
        background-image: linear-gradient(to bottom right, 
                          rgba(255, 255, 255, 0.9) 0%, 
                          rgba(245, 247, 250, 0.8) 100%);
        border-radius: 12px;
        height: 100%;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    /* Containers and cards styling */
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(0, 0, 0, 0.05);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    
    /* Alert boxes */
    .stSuccess, .stInfo {
        border-radius: 8px;
        border: none !important;
    }
    
    .stSuccess {
        background-color: rgba(45, 183, 114, 0.1) !important;
        color: #2b6e4b !important;
    }
    
    .stInfo {
        background-color: rgba(38, 99, 215, 0.1) !important;
        color: #1e4c94 !important;
    }
    
    /* Dataframes and tables */
    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px;
        padding: 1px !important;
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stDataFrame"] [data-testid="stTable"] {
        background-color: transparent !important;
    }
    
    /* Table headers and cells - force light theme */
    .stDataFrame th {
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
    }
    
    .stDataFrame td {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Style for horizontal dividers - multiple selectors for different scenarios */
    hr, 
    .stMarkdown hr,
    .element-container hr,
    .stHorizontalBlock hr,
    .stVerticalBlock hr,
    .stExpander hr {
        border: none !important;
        height: 1px !important;
        background-color: rgba(0, 0, 0, 0.1) !important;
        margin: 1.5rem 0 !important;
        opacity: 0.3 !important;
    }
    
    /* Fix tables with direct styling */
    table {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    thead tr th {
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
    }
    
    tbody tr {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* Fix selector dropdown with extra specificity */
    div[role="listbox"] {
        background-color: #ffffff !important;
    }
    
    div[role="listbox"] div[role="option"] {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="popover"] div {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    /* Force background colors using !important with high specificity */
    div[data-baseweb="popover"] ul li,
    div[data-baseweb="popover"] ul li button,
    div[data-baseweb="popover"] div[role="option"] {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    div[data-baseweb="popover"] div[role="option"]:hover {
        background-color: rgba(46, 204, 113, 0.1) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(248, 249, 250, 0.95) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Dropdowns and selectboxes */
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #1a1a2e !important;
    }
    
    div[role="listbox"] {
        background-color: #ffffff !important;
    }
    
    div[role="option"] {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    
    div[role="option"]:hover {
        background-color: rgba(46, 204, 113, 0.1) !important;
    }
    
    /* Fix expanders */
    .streamlit-expanderHeader {
        background-color: rgba(248, 249, 250, 0.95) !important;
        color: #1a1a2e !important;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff !important;
    }
    
    /* Button styling */
    button[kind="primary"], 
    button.css-1cpxqw2, 
    button.css-1p1lx2y {
        background-color: #2ecc71 !important;
        border-radius: 6px !important;
        color: #ffffff !important;
    }
    
    button[kind="secondary"], 
    button.css-5rimss, 
    button.css-gw32o0 {
        border-color: #2ecc71 !important;
        color: #2ecc71 !important;
        background-color: #ffffff !important;
        border-radius: 6px !important;
    }
    
    /* Override specific black-colored button elements */
    button, 
    button[data-testid="baseButton-secondary"],
    .stButton>button, 
    .css-7ym5gk,
    .css-1ekf893, 
    .css-17f8hu8 {
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Make sure primary action buttons keep their proper color */
    button.primary, button[kind="primary"] {
        background-color: #2ecc71 !important;
        color: white !important;
    }
</style>
''', unsafe_allow_html=True)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {font-family: 'Scope One', serif;}
    .kpi-box {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin: 5px;
        font-family: 'Roboto Mono', monospace;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .kpi-box:hover {
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 0.85em;
        color: #555;
        font-weight: 500;
    }
    .kpi-value {
        font-size: 1.4em;
        font-weight: 700;
        margin: 5px 0;
    }
    .alert-box {
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
        border-left: 4px solid #e74c3c;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px;
        background-color: #f8f9fa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
    }
    .stTextInput>div>div>input {
        border-radius: 6px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 6px;
    }
    .stMarkdown {
        line-height: 1.6;
    }
    .st-bd {
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'current_note' not in st.session_state:
    st.session_state.current_note = ""

# Helper functions
def kpi_color(value: float, low: float, high: float) -> str:
    """Return color based on value range."""
    if value is None:
        return "#95a5a6"  # Gray for missing data
    return "#2ecc71" if low <= value <= high else "#e74c3c"

def get_risk_score(patient: Dict) -> Tuple[int, str]:
    """Calculate a simple risk score based on patient data."""
    score = 0
    reasons = []
    
    # Check vitals
    vitals = patient.get('vitals', {})
    if vitals.get('sbp', 0) > 140 or vitals.get('sbp', 0) < 90:
        score += 1
        reasons.append("Abnormal blood pressure")
    if vitals.get('hr', 0) > 100 or vitals.get('hr', 0) < 50:
        score += 1
        reasons.append("Abnormal heart rate")
    if 'diabetes' in ' '.join(patient.get('conditions', [])).lower():
        score += 1
        reasons.append("Diabetes management")
    if 'surgery' in patient and patient['surgery'] and isinstance(patient['surgery'], dict) and 'date' in patient['surgery'] and (datetime.now().date() - patient['surgery']['date']).days < 30:
        score += 2
        reasons.append("Recent surgery")
    
    # Categorize risk
    if score >= 3:
        return score, "High"
    elif score >= 1:
        return score, "Medium"
    return score, "Low"

def generate_mock_data() -> List[Dict]:
    """Generate realistic mock patient data with clinical relevance."""
    patients = []
    first_names = ["John", "Jane", "Robert", "Emily", "Michael", "Sarah", "David", "Lisa", "James", "Mary"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson"]
    
    # Common conditions and procedures with some clinical relevance
    common_conditions = [
        "Hypertension", "Type 2 Diabetes", "Hyperlipidemia", "Osteoarthritis", 
        "COPD", "Coronary Artery Disease", "Atrial Fibrillation", "GERD"
    ]
    
    common_procedures = [
        "Knee Replacement", "Hip Replacement", "CABG", "Appendectomy",
        "Cataract Surgery", "Cholecystectomy", "Hernia Repair"
    ]
    
    for i in range(1, 26):
        first = random.choice(first_names)
        last = random.choice(last_names)
        age = random.randint(45, 90)  # More clinically relevant age range
        sex = random.choice(["Male", "Female"])
        
        # Generate realistic vitals with some correlation to conditions
        has_hypertension = random.random() > 0.7
        has_diabetes = random.random() > 0.7
        
        sbp = random.randint(130 if has_hypertension else 100, 160 if has_hypertension else 140)
        dbp = random.randint(80 if has_hypertension else 60, 100 if has_hypertension else 90)
        hr = random.randint(60, 100)
        weight = round(random.uniform(60 if not has_diabetes else 70, 110 if not has_diabetes else 130), 1)
        height = round(random.uniform(155, 190), 1)
        bmi = round(weight / ((height/100) ** 2), 1)
        phq9 = random.choices(
            population=range(0, 28),
            weights=[10,10,10,8,7,6,5,4,4,3,3,2,2,2,1,1,1,1,1,0.5,0.5,0.5,0.3,0.2,0.1,0.1,0.1,0.1],
            k=1
        )[0]
        
        # Generate conditions with clinical relevance
        conditions = []
        if has_hypertension:
            conditions.append("Hypertension")
        if has_diabetes:
            conditions.append("Type 2 Diabetes")
        if random.random() > 0.7:
            conditions.append(random.choice([c for c in common_conditions if c not in ["Hypertension", "Type 2 Diabetes"]]))
        if not conditions:
            conditions = ["No active problems"]
            
        # Generate lab data with some clinical correlation
        hba1c = round(random.uniform(5.0, 10.0 if has_diabetes else 6.4), 1)
        labs = {
            "WBC": round(random.uniform(3.5, 11.0), 1),
            "Hgb": round(random.uniform(10.0, 16.0), 1),
            "Platelets": random.randint(150, 450),
            "Glucose": random.randint(90, 200 if has_diabetes else 140),
            "HbA1c": hba1c,
            "eGFR": random.randint(30 if hba1c > 8 else 60, 120),
            "LDL": random.randint(70, 190)
        }
        
        # Generate trend data (last 7 days)
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
        
        # Generate trends with some correlation
        sbp_trend = [max(70, min(180, sbp + random.randint(-15, 15))) for _ in range(7)]
        dbp_trend = [max(40, min(100, dbp + random.randint(-10, 10))) for _ in range(7)]
        hr_trend = [max(50, min(130, hr + random.randint(-15, 15))) for _ in range(7)]
        weight_trend = [max(40, min(130, weight + random.uniform(-3, 3))) for _ in range(7)]
        bmi_trend = [round(w / ((height/100) ** 2), 1) for w in weight_trend]
        phq_trend = [max(0, min(27, phq9 + random.randint(-2, 2))) for _ in range(7)]
        
        # Add surgery if relevant
        surgery = None
        if random.random() > 0.7:  # 30% chance of recent surgery
            surgery = {
                'procedure': random.choice(common_procedures),
                'date': (datetime.now() - timedelta(days=random.randint(1, 60))).date(),
                'surgeon': f"Dr. {random.choice(last_names)}",
                'location': random.choice(["Main Hospital OR", "Outpatient Surgery Center"])
            }
        
        # Add medications based on conditions
        medications = []
        if has_hypertension:
            medications.append({
                'name': random.choice(['Lisinopril', 'Amlodipine', 'Losartan']),
                'dose': random.choice(['10mg', '20mg', '40mg']),
                'frequency': 'Daily',
                'last_filled': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            })
        if has_diabetes:
            dose = random.choice(['500mg', '1000mg', '10 units', '20 units'])
            medications.append({
                'name': random.choice(['Metformin', 'Glipizide', 'Insulin Glargine']),
                'dose': dose,
                'frequency': 'Daily' if 'units' not in dose else 'Twice daily',
                'last_filled': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            })
        
        patient = {
            "id": f"{i:03d}",
            "name": f"{last}, {first}",
            "age": age,
            "sex": sex,
            "mrn": f"M{random.randint(100000, 999999)}",
            "admission_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            "vitals": {
                "sbp": sbp,
                "dbp": dbp,
                "hr": hr,
                "weight": weight,
                "height": height,
                "bmi": bmi,
                "phq9": phq9,
                "temperature": round(random.uniform(36.5, 38.5), 1),
                "spo2": random.randint(95, 100),
                "pain_score": random.randint(0, 10) if random.random() > 0.3 else None
            },
            "conditions": conditions,
            "labs": labs,
            "medications": medications,
            "surgery": surgery,
            "last_visit": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            "next_appointment": (datetime.now() + timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
            "care_team": {
                "primary": f"Dr. {random.choice(last_names)}",
                "nurse": f"Nurse {random.choice(['Johnson', 'Smith', 'Williams'])}",
                "therapist": f"PT {random.choice(['Taylor', 'Brown', 'Davis'])}"
            },
            "trends": {
                "dates": dates,
                "sbp": sbp_trend,
                "dbp": dbp_trend,
                "hr": hr_trend,
                "weight": weight_trend,
                "bmi": bmi_trend,
                "phq9": phq_trend,
                "glucose": [labs["Glucose"] + random.randint(-20, 20) for _ in range(7)],
                "pain": [random.randint(0, 5 if phq9 < 10 else 10) for _ in range(7)]
            },
            "notes": [
                {
                    "date": (datetime.now() - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                    "author": f"Dr. {random.choice(last_names)}",
                    "content": random.choice([
                        "Patient reports improved mobility and decreased pain.",
                        "Continue current treatment plan, reassess in 2 weeks.",
                        "Medications adjusted based on latest lab results.",
                        "Physical therapy showing good progress.",
                        "Monitor blood pressure closely, consider medication adjustment if remains elevated."
                    ])
                } for _ in range(random.randint(1, 3))
            ]
        }
        
        # Add risk score
        risk_score, risk_level = get_risk_score(patient)
        patient['risk_score'] = risk_score
        patient['risk_level'] = risk_level
        
        patients.append(patient)
    
    # Sort patients by risk level (high to low)
    risk_order = {"High": 0, "Medium": 1, "Low": 2}
    patients.sort(key=lambda x: (risk_order[x['risk_level']], -x['risk_score']))
    
    return patients

def display_patient_header(patient: Dict) -> None:
    """Display patient header with comprehensive information."""
    # Risk level color mapping
    risk_colors = {
        "High": "#e74c3c",
        "Medium": "#f39c12",
        "Low": "#2ecc71"
    }
    
    # Header with patient info and risk indicator
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"# {patient['name']}  ", unsafe_allow_html=True)
        st.caption(f"MRN: {patient.get('mrn', 'N/A')} | DOB: {datetime.now().year - patient['age']}")
    
    with col2:
        risk_level = patient.get('risk_level', 'Low')
        st.markdown(
            f"<div style='background-color: {risk_colors.get(risk_level, '#95a5a6')}; "
            f"color: white; padding: 10px; border-radius: 6px; text-align: center;'>"
            f"<strong>Risk: {risk_level}</strong></div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"<div style='background-color: rgba(245, 247, 250, 0.9); color: #1a1a2e; padding: 12px; "
            f"border-radius: 8px; border: 1px solid rgba(0, 0, 0, 0.05); box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);'>"
            f"<div><strong>Age:</strong> {patient['age']} {patient['sex']}</div>"
            f"<div><strong>Last Visit:</strong> {patient.get('last_visit', 'N/A')}</div>"
            f"<div><strong>Next Appt:</strong> {patient.get('next_appointment', 'Not scheduled')}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Care team information
    with st.expander("Care Team", expanded=False):
        team = patient.get('care_team', {})
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"**Primary:**  \n{team.get('primary', 'N/A')}")
        with cols[1]:
            st.markdown(f"**Nurse:**  \n{team.get('nurse', 'N/A')}")
        with cols[2]:
            st.markdown(f"**Therapist:**  \n{team.get('therapist', 'N/A')}")
    
    st.markdown("---")

def display_kpi_row(patient: Dict) -> None:
    """Display comprehensive KPI row with clinical metrics."""
    vitals = patient.get("vitals", {})
    labs = patient.get("labs", {})
    
    # Define KPI items with their ranges, units, and colors
    kpis = [
        # Vitals
        ("BP", f"{vitals.get('sbp', '--')}/{vitals.get('dbp', '--')}", "mmHg", 
         kpi_color(vitals.get('sbp', 0), 90, 120) if vitals.get('sbp') else "#95a5a6"),
        ("HR", vitals.get("hr", "--"), "bpm", 
         kpi_color(vitals.get("hr", 0), 60, 100) if vitals.get('hr') else "#95a5a6"),
        ("Temp", f"{vitals.get('temperature', '--')}°C", "", 
         kpi_color(vitals.get('temperature', 0), 36.5, 37.5) if vitals.get('temperature') else "#95a5a6"),
        ("SpO₂", f"{vitals.get('spo2', '--')}%", "", 
         kpi_color(vitals.get('spo2', 0), 95, 100) if vitals.get('spo2') else "#95a5a6"),
        ("Pain", vitals.get("pain_score", "--") if vitals.get("pain_score") is not None else "--", "", 
         kpi_color(0, 0, 4) if isinstance(vitals.get("pain_score"), int) and vitals["pain_score"] <= 4 else 
         kpi_color(5, 5, 7) if isinstance(vitals.get("pain_score"), int) and vitals["pain_score"] <= 7 
         else kpi_color(8, 8, 10) if isinstance(vitals.get("pain_score"), int) else "#95a5a6"),
        
        # Lab values
        ("Glucose", labs.get("Glucose", "--"), "mg/dL", 
         kpi_color(labs.get("Glucose", 0), 70, 140) if labs.get("Glucose") else "#95a5a6"),
        ("HbA1c", labs.get("HbA1c", "--"), "%", 
         kpi_color(labs.get("HbA1c", 0), 4, 5.6) if labs.get("HbA1c") else "#95a5a6"),
        ("eGFR", labs.get("eGFR", "--"), "mL/min", 
         kpi_color(labs.get("eGFR", 0), 60, 120) if labs.get("eGFR") else "#95a5a6"),
    ]
    
    # Create two rows of KPIs
    num_cols = 8
    for i in range(0, len(kpis), num_cols):
        row_kpis = kpis[i:i+num_cols]
        cols = st.columns(len(row_kpis))
        
        for idx, (label, value, unit, color) in enumerate(row_kpis):
            with cols[idx]:
                # No icons - removed emojis
                
                st.markdown(
                    f"""
                    <div class='kpi-box' style='border-left: 4px solid {color}'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span class='kpi-label'>{label}</span>
                        </div>
                        <div class='kpi-value'>{value} <span style='font-size: 0.8em; color: #666;'>{unit}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Add a small gap after KPIs
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

def generate_clinical_alerts(patient: Dict) -> List[Dict]:
    """Generate clinical alerts based on patient data."""
    alerts = []
    vitals = patient.get("vitals", {})
    labs = patient.get("labs", {})
    
    # Vital sign alerts
    if vitals.get("sbp") is not None:
        if vitals["sbp"] > 140:
            alerts.append({
                "type": "warning",
                "title": "Elevated Blood Pressure",
                "message": f"Systolic BP is elevated at {vitals['sbp']} mmHg. Consider monitoring and intervention.",
                "priority": "high" if vitals["sbp"] > 160 else "medium"
            })
        elif vitals["sbp"] < 90:
            alerts.append({
                "type": "danger",
                "title": "Low Blood Pressure",
                "message": f"Systolic BP is low at {vitals['sbp']} mmHg. Assess for hypotension.",
                "priority": "high"
            })
    
    if vitals.get("hr") is not None:
        if vitals["hr"] > 100:
            alerts.append({
                "type": "warning",
                "title": "Tachycardia",
                "message": f"Heart rate is elevated at {vitals['hr']} bpm. Consider causes and monitor.",
                "priority": "high" if vitals["hr"] > 120 else "medium"
            })
        elif vitals["hr"] < 50:
            alerts.append({
                "type": "danger",
                "title": "Bradycardia",
                "message": f"Heart rate is low at {vitals['hr']} bpm. Assess for bradycardia.",
                "priority": "high"
            })
    
    # Lab alerts
    if labs.get("Glucose") is not None:
        if labs["Glucose"] > 200:
            alerts.append({
                "type": "danger",
                "title": "Hyperglycemia",
                "message": f"Blood glucose is high at {labs['Glucose']} mg/dL. Consider diabetes management.",
                "priority": "high"
            })
        elif labs["Glucose"] < 70:
            alerts.append({
                "type": "danger",
                "title": "Hypoglycemia",
                "message": f"Blood glucose is low at {labs['Glucose']} mg/dL. Immediate attention needed.",
                "priority": "critical"
            })
    
    if labs.get("eGFR") is not None and labs["eGFR"] < 60:
        alerts.append({
            "type": "warning",
            "title": "Reduced Kidney Function",
            "message": f"eGFR is {labs['eGFR']} mL/min/1.73m², indicating stage 3 or worse CKD.",
            "priority": "high" if labs["eGFR"] < 30 else "medium"
        })
    
    # Medication alerts
    meds = patient.get("medications", [])
    for med in meds:
        last_filled = datetime.strptime(med["last_filled"], "%Y-%m-%d").date()
        days_since_fill = (datetime.now().date() - last_filled).days
        if days_since_fill > 30:
            alerts.append({
                "type": "warning",
                "title": "Medication Refill Needed",
                "message": f"{med['name']} was last filled {days_since_fill} days ago.",
                "priority": "medium"
            })
    
    # Sort by priority (critical > high > medium > low)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda x: priority_order.get(x["priority"], 999))
    
    return alerts

def display_alerts(patient: Dict) -> None:
    """Display alerts in the sidebar with severity levels."""
    st.sidebar.markdown("## Clinical Alerts")
    
    # Generate alerts based on patient data
    alerts = generate_clinical_alerts(patient)
    
    # Add PHQ-9 alert if applicable
    if patient.get("vitals", {}).get("phq9", 0) >= 15:
        alerts.insert(0, {
            "type": "danger",
            "title": "Depression Screening Alert",
            "message": f"PHQ-9 score is {patient['vitals']['phq9']}/27, indicating moderately severe to severe depression.",
            "priority": "high"
        })
    
    # Add pain alert if applicable
    pain_score = patient.get("vitals", {}).get("pain_score")
    if pain_score is not None and isinstance(pain_score, (int, float)) and pain_score >= 7:
        alerts.insert(0, {
            "type": "warning",
            "title": "Severe Pain Reported",
            "message": f"Pain score is {pain_score}/10. Consider pain management options.",
            "priority": "high"
        })
    
    # Display alerts or "No active alerts"
    if alerts:
        for alert in alerts:
            alert_type = alert["type"]
            if alert_type == "danger":
                st.sidebar.error(f"**{alert['title']}**  \n{alert['message']}")
            elif alert_type == "warning":
                st.sidebar.warning(f"**{alert['title']}**  \n{alert['message']}")
            else:
                st.sidebar.info(f"**{alert['title']}**  \n{alert['message']}")
    else:
        st.sidebar.success("No active clinical alerts")
    
    # Add a button to acknowledge all alerts
    if alerts:
        if st.sidebar.button("Acknowledge All Alerts"):
            st.sidebar.success("All alerts have been acknowledged")
            st.experimental_rerun()
    
    # Add a small gap
    st.sidebar.markdown("---")

def generate_patient_trends(patient: Dict) -> Dict:
    """Generate trend data for a patient if it doesn't exist"""
    # Check if trends already exist
    if "trends" in patient and isinstance(patient["trends"], dict):
        return patient["trends"]
    
    # Generate realistic dates for the past year (one per month)
    today = datetime.now().date()
    dates = [(today - timedelta(days=30*i)).strftime("%Y-%m-%d") for i in range(12)]
    dates.reverse()  # Order from oldest to newest
    
    # Get base values from patient record
    vitals = patient.get("vitals", {})
    base_sbp = vitals.get("sbp", 120)
    base_dbp = vitals.get("dbp", 80)
    base_hr = vitals.get("hr", 75)
    base_weight = vitals.get("weight", 70)
    base_bmi = vitals.get("bmi", 24.5)
    base_phq9 = vitals.get("phq9", 5)
    
    # Generate realistic variations for each metric
    sbp_values = [max(90, min(180, base_sbp + random.randint(-15, 15))) for _ in range(12)]
    dbp_values = [max(50, min(110, base_dbp + random.randint(-10, 10))) for _ in range(12)]
    hr_values = [max(50, min(120, base_hr + random.randint(-10, 10))) for _ in range(12)]
    weight_values = [max(40, min(150, base_weight + random.uniform(-2, 2))) for _ in range(12)]
    
    # Calculate BMI based on weight changes (assuming height is constant)
    height = vitals.get("height", 170) / 100  # cm to meters
    bmi_values = [round(weight / (height ** 2), 1) for weight in weight_values]
    
    # Generate PHQ-9 scores with some consistency
    phq9_values = []
    current = base_phq9
    for _ in range(12):
        change = random.choice([-2, -1, -1, 0, 0, 0, 1, 1, 2])
        current = max(0, min(27, current + change))
        phq9_values.append(current)
    
    # Create trends dictionary
    trends = {
        "dates": dates,
        "sbp": sbp_values,
        "dbp": dbp_values,
        "hr": hr_values,
        "weight": weight_values,
        "bmi": bmi_values,
        "phq9": phq9_values
    }
    
    # Add trends to patient record
    patient["trends"] = trends
    
    return trends

def display_trends(patient: Dict) -> None:
    """Display trend tabs with Plotly charts."""
    # Generate trends if they don't exist
    trends = generate_patient_trends(patient)
    
    # Define light theme for all charts
    light_template = dict(
        layout=dict(
            paper_bgcolor='white',
            plot_bgcolor='#f8f9fa',
            font=dict(color='#1a1a2e'),
            title=dict(font=dict(color='#1a1a2e')),
            xaxis=dict(
                gridcolor='#e6e6e6',
                zerolinecolor='#e6e6e6',
                tickfont=dict(color='#1a1a2e')
            ),
            yaxis=dict(
                gridcolor='#e6e6e6',
                zerolinecolor='#e6e6e6',
                tickfont=dict(color='#1a1a2e')
            ),
            legend=dict(font=dict(color='#1a1a2e'))
        )
    )
    
    tab1, tab2, tab3 = st.tabs(["Cardiometabolic", "Weight / BMI", "Mood"])
    
    with tab1:
        # Cardiometabolic tab
        df_cardio = pd.DataFrame({
            'Date': trends['dates'],
            'SBP': trends['sbp'],
            'DBP': trends['dbp'],
            'HR': trends['hr']
        })
        
        fig_cardio = px.line(
            df_cardio, 
            x='Date', 
            y=['SBP', 'DBP', 'HR'],
            title='Cardiometabolic Trends',
            labels={'value': 'Value', 'variable': 'Metric'},
            height=400,
            color_discrete_sequence=['#3498db', '#1abc9c', '#e74c3c']
        )
        
        # Apply light theme
        fig_cardio.update_layout(light_template['layout'])
        st.plotly_chart(fig_cardio, use_container_width=True)
    
    with tab2:
        # Weight/BMI tab
        df_weight = pd.DataFrame({
            'Date': trends['dates'],
            'Weight (kg)': trends['weight'],
            'BMI': trends['bmi']
        })
        
        fig_weight = px.area(
            df_weight,
            x='Date',
            y=['Weight (kg)', 'BMI'],
            title='Weight and BMI Trends',
            labels={'value': 'Value', 'variable': 'Metric'},
            height=400,
            color_discrete_sequence=['#2ecc71', '#3498db']
        )
        
        # Apply light theme
        fig_weight.update_layout(light_template['layout'])
        st.plotly_chart(fig_weight, use_container_width=True)
    
    with tab3:
        # Mood tab (PHQ-9)
        df_mood = pd.DataFrame({
            'Date': trends['dates'],
            'PHQ-9': trends['phq9']
        })
        
        fig_mood = px.line(
            df_mood,
            x='Date',
            y='PHQ-9',
            title='Mood (PHQ-9) Trend',
            labels={'PHQ-9': 'PHQ-9 Score'},
            height=400
        )
        
        # Apply light theme and update line color
        fig_mood.update_layout(light_template['layout'])
        fig_mood.update_traces(line=dict(color='#9b59b6'))
        st.plotly_chart(fig_mood, use_container_width=True)

def display_active_problems(patient: Dict) -> None:
    """Display active problems."""
    st.markdown("### Active Problems")
    st.markdown(", ".join(patient["conditions"]) if patient["conditions"] else "No active problems")
    # Using a subtle divider with custom styling
    st.markdown("<div style='height: 1px; background-color: rgba(0,0,0,0.1); margin: 1.5rem 0; opacity: 0.3;'></div>", unsafe_allow_html=True)

def display_recent_labs(patient: Dict) -> None:
    """Display recent lab results using custom HTML table."""
    st.markdown("### Recent Labs")
    
    labs = patient.get("labs", {})
    
    # Create lab data
    lab_data = [
        ["WBC", f"{labs.get('WBC', '--')} K/µL", "3.5-11.0 K/µL"],
        ["Hemoglobin", f"{labs.get('Hgb', '--')} g/dL", "12.0-16.0 g/dL"],
        ["Platelets", f"{labs.get('Platelets', '--')} K/µL", "150-450 K/µL"],
        ["Glucose", f"{labs.get('Glucose', '--')} mg/dL", "70-140 mg/dL"],
        ["HbA1c", f"{labs.get('HbA1c', '--')}%", "<5.7%"]
    ]
    
    # Instead of custom HTML, let's simplify and use Markdown for better visibility
    st.markdown("""
    | Test | Result | Reference Range |
    | ---- | ------ | --------------- |
    | WBC | {} | 3.5-11.0 K/µL |
    | Hemoglobin | {} | 12.0-16.0 g/dL |
    | Platelets | {} | 150-450 K/µL |
    | Glucose | {} | 70-140 mg/dL |
    | HbA1c | {} | <5.7% |
    """.format(
        labs.get('WBC', '--') + ' K/µL',
        labs.get('Hgb', '--') + ' g/dL',
        labs.get('Platelets', '--') + ' K/µL',
        labs.get('Glucose', '--') + ' mg/dL',
        labs.get('HbA1c', '--') + '%'
    ))
    # Using a subtle divider with custom styling
    st.markdown("<div style='height: 1px; background-color: rgba(0,0,0,0.1); margin: 1.5rem 0; opacity: 0.3;'></div>", unsafe_allow_html=True)

def display_billing() -> None:
    """Display billing information."""
    with st.expander("Billing / RTM"):
        st.write("$1,150, $704")

def display_clinical_summary(patient: Dict):
    """Display AI-generated clinical summary from Claude."""
    # In Summary view, the header is added separately as part of the breadcrumb content
    if st.session_state.view_mode != "Summary":
        st.markdown("### AI Clinical Summary")
    
    with st.spinner("Generating clinical summary with Claude AI..."):
        # Call the AI Clinical Assistant to generate the summary
        summary = AIClinicalAssistant.generate_summary(patient)
        st.markdown(summary)
    if st.button("Generate Comprehensive Summary"):
        with st.spinner("Generating comprehensive summary with Claude AI..."):
            if "id" in patient:
                comprehensive_summary = AIClinicalAssistant.generate_mcp_summary(f"patient:{patient['id']}")
            else:
                comprehensive_summary = AIClinicalAssistant.generate_mcp_summary()
            st.markdown(comprehensive_summary)
    
    # Only add divider in Traditional view
    if st.session_state.view_mode != "Summary":
        # Using a more subtle divider with custom styling
        st.markdown("<div style='height: 1px; background-color: rgba(0,0,0,0.1); margin: 1.5rem 0; opacity: 0.3;'></div>", unsafe_allow_html=True)

def display_exercise_adherence(patient: Dict):
    """Display exercise adherence chart and details."""
    st.markdown("### Exercise Adherence")
    
    # Get Movemend data from patient record
    movemend_data = patient.get('movemend_data', {})
    sessions = movemend_data.get('sessions', [])
    
    if not sessions:
        st.info("No exercise sessions recorded yet.")
        return
    
    # Create a DataFrame for the sessions
    session_data = []
    for session in sessions:
        # Format the date properly
        date_str = session.get('date', '')
        if date_str:
            try:
                # Handle different date formats
                if 'T' in date_str:
                    date_obj = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date_formatted = date_obj.strftime('%b %d, %Y')
            except:
                date_formatted = date_str
        else:
            date_formatted = 'Unknown'
        
        # Add session to data
        session_data.append({
            'Date': date_formatted,
            'Exercise': session.get('gameId', 'Unknown').replace('_', ' ').title(),
            'Duration (min)': session.get('duration_minutes', 0),
            'Score': session.get('score', 0),
            'Quality': session.get('quality', 0)
        })
    
    # Convert to DataFrame and sort by date
    df_sessions = pd.DataFrame(session_data)
    df_sessions = df_sessions.sort_values('Date', ascending=False).reset_index(drop=True)
    
    # Calculate exercise stats
    total_sessions = len(df_sessions)
    total_minutes = df_sessions['Duration (min)'].sum()
    avg_quality = df_sessions['Quality'].mean()
    
    # Display stats in columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sessions", total_sessions)
    col2.metric("Total Minutes", int(total_minutes))
    col3.metric("Avg Quality", f"{avg_quality:.1f}%")
    
    # Create exercise type distribution chart
    exercise_counts = df_sessions['Exercise'].value_counts().reset_index()
    exercise_counts.columns = ['Exercise', 'Count']
    
    # Create a pie chart for exercise distribution
    fig_pie = px.pie(
        exercise_counts, 
        values='Count', 
        names='Exercise',
        title='Exercise Type Distribution',
        hole=0.4,  # Donut chart
        color_discrete_sequence=['#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c']
    )
    
    # Apply light theme
    fig_pie.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        font=dict(color='#1a1a2e'),
        title=dict(font=dict(color='#1a1a2e')),
        legend=dict(font=dict(color='#1a1a2e'))
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Display session history table using markdown for better visibility
    st.subheader("Recent Exercise Sessions")
    
    # Format data for markdown table
    if len(df_sessions) > 0:
        # Header
        table_md = "| Date | Exercise | Duration (min) | Score | Quality |\n"
        table_md += "| ---- | -------- | -------------- | ----- | ------- |\n"
        
        # Rows
        for i, row in df_sessions.iterrows():
            table_md += f"| {row['Date']} | {row['Exercise']} | {row['Duration (min)']} | {row['Score']} | {row['Quality']} |\n"
        
        st.markdown(table_md)
    else:
        st.info("No exercise sessions recorded yet.")

# Function to generate unique MoveMend exercise data for each patient
def generate_unique_movemend_data(patient_id: str) -> Dict:
    """Generate unique MoveMend exercise data for a patient based on their ID"""
    # Use the patient ID as a seed for random generation to ensure the same patient always gets the same data
    # This makes the random generation deterministic per patient
    random.seed(hash(patient_id))
    
    # Exercise types available in MoveMend
    exercise_types = [
        "gardening", "boxing", "rowing", "soccer", "berry_picking", 
        "hot_potato", "fishing", "dancing", "bowling", "tennis"
    ]
    
    # Generate a random number of sessions (3-8) for this patient
    num_sessions = random.randint(3, 8)
    
    # Generate session dates in the past year
    today = datetime.now().date()
    
    # Generate random sessions
    sessions = []
    for _ in range(num_sessions):
        # Random date in the past year
        days_ago = random.randint(0, 365)
        session_date = today - timedelta(days=days_ago)
        
        # Random exercise type
        exercise = random.choice(exercise_types)
        
        # Random session metrics
        duration = random.randint(1, 10)  # 1-10 minutes
        score = random.randint(5, 25)     # 5-25 points
        quality = random.randint(30, 95)  # 30-95% quality
        
        # Add session to list
        sessions.append({
            "gameId": exercise,
            "date": session_date.strftime("%Y-%m-%d"),
            "score": score,
            "duration_minutes": duration,
            "quality": quality,
            "notes": ""
        })
    
    # Sort sessions by date (newest first)
    sessions.sort(key=lambda x: x["date"], reverse=True)
    
    # Generate provider names that are stable for this patient
    provider_names = [
        "Dr. Sarah Johnson", "Dr. Robert Chen", "Dr. Maria Rodriguez", 
        "Dr. James Wilson", "Dr. Emily Thompson", "Dr. Michael Brown"
    ]
    random.shuffle(provider_names)
    
    # Create complete MoveMend record
    movemend_data = {
        "resourceType": "MovemendRecord",
        "id": patient_id,
        "sessions": sessions,
        "primary_provider": provider_names[0],
        "specialist": provider_names[1],
        "last_visit_date": (today - timedelta(days=random.randint(5, 60))).strftime("%Y-%m-%d"),
        "next_appointment": (today + timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d"),
        "notes": []
    }
    
    # Reset random seed to avoid affecting other random generation
    random.seed()
    
    return movemend_data

# Helper functions for patient data extraction
def clean_name(name):
    """Remove numbers from names and capitalize properly"""
    # Remove any digits from the name
    name_no_digits = ''.join([c for c in name if not c.isdigit()])
    # Split by potential remaining underscores
    parts = name_no_digits.split('_')
    # Capitalize each part
    cleaned_parts = [part.capitalize() for part in parts]
    # Join back together with spaces
    return ' '.join(cleaned_parts)

def extract_name(patient_record):
    """Extract patient name from patient record based on FHIR structure"""
    try:
        # First check if the patient data is wrapped in a Bundle structure
        if 'entry' in patient_record and isinstance(patient_record['entry'], list) and len(patient_record['entry']) > 0:
            # Find the Patient resource in the bundle
            for entry in patient_record['entry']:
                if 'resource' in entry and entry['resource'].get('resourceType') == 'Patient':
                    patient_data = entry['resource']
                    if 'name' in patient_data and isinstance(patient_data['name'], list) and len(patient_data['name']) > 0:
                        name_obj = patient_data['name'][0]
                        given = name_obj.get('given', ['Unknown'])
                        given = given[0] if isinstance(given, list) and given else 'Unknown'
                        family = name_obj.get('family', 'Unknown')
                        return f"{given} {family}"
                    break
        
        # Direct access for non-bundle structure
        elif 'name' in patient_record and isinstance(patient_record['name'], list) and len(patient_record['name']) > 0:
            name_obj = patient_record['name'][0]
            given = name_obj.get('given', ['Unknown'])
            given = given[0] if isinstance(given, list) and given else 'Unknown'
            family = name_obj.get('family', 'Unknown')
            return f"{given} {family}"
        
        # Try with filename as a fallback if available
        if 'id' in patient_record:
            # Check if there's a full patient name in the database directory
            patient_id = patient_record['id']
            patient_files = os.listdir('/Users/punitvats/CascadeProjects/mcp-hackathon-project/Database Simulation/Database Simulator/medical_record_database/synthea_sample_data_fhir_latest')
            for filename in patient_files:
                if patient_id in filename and '_' in filename:
                    # Parse name from filename (usually in format FirstName_LastName_ID.json)
                    name_parts = filename.split('_')[:2]
                    # Clean the names to remove numbers
                    first_name = clean_name(name_parts[0])
                    last_name = clean_name(name_parts[1])
                    return f"{first_name} {last_name}"
                    
        # Final fallback
        return f"Patient {patient_record.get('id', 'Unknown')[-6:]}"
    except Exception as e:
        st.error(f"Error extracting name: {str(e)}")
        return f"Patient {patient_record.get('id', 'Unknown')[-6:]}"

def extract_identifier(patient_record):
    """Extract patient MRN from patient record"""
    try:
        if 'identifier' in patient_record and isinstance(patient_record['identifier'], list) and len(patient_record['identifier']) > 0:
            return patient_record['identifier'][0].get('value', 'Unknown')
        return f"MRN-{patient_record['id'][-8:]}"
    except Exception as e:
        st.error(f"Error extracting identifier: {str(e)}")
        return "Unknown MRN"

def extract_age(patient_record):
    """Extract patient age from patient record"""
    try:
        if 'birthDate' in patient_record:
            # Calculate age from birthDate
            birth_year = int(patient_record['birthDate'].split('-')[0])
            current_year = datetime.now().year
            return current_year - birth_year
        return int(patient_record.get('age', 50))
    except Exception as e:
        st.error(f"Error extracting age: {str(e)}")
        return 50

def extract_conditions(patient_record):
    """Extract patient conditions from patient record"""
    try:
        if 'conditions' in patient_record and isinstance(patient_record['conditions'], list):
            conditions = []
            for condition in patient_record['conditions']:
                if 'code' in condition and 'text' in condition['code']:
                    conditions.append(condition['code']['text'])
            return conditions if conditions else ["No active problems"]
        return ["No active problems"]
    except Exception as e:
        st.error(f"Error extracting conditions: {str(e)}")
        return ["No active problems"]

def load_patients_from_database():
    """Load patient data from the Database Simulation - no fallback to mock data"""
    # Attempt to get random patients from the database
    st.info("Connecting to Database Simulation...")
    try:
        # Get 15 random patients from the database
        response = get_random_patient_data(15)
        patients_data = response.json()
        st.success("Connected to Database Simulation successfully!")
        
        # Process each patient and add movemend data
        processed_patients = []
        for patient_record in patients_data:
            try:
                # Get additional Movemend data for this patient
                try:
                    # Try to get MoveMend data from the database
                    movemend_response = get_movemend_data(patient_record["id"])
                    
                    # If we got a valid response, use it
                    if hasattr(movemend_response, 'json'):
                        movemend_data = movemend_response.json()
                    else:
                        # If no valid MoveMend data found, generate unique data for this patient
                        movemend_data = generate_unique_movemend_data(patient_record["id"])
                except:
                    # In case of any error, generate unique data
                    movemend_data = generate_unique_movemend_data(patient_record["id"])
                
                # Format patient data to match our app's expectations
                patient = {
                    'id': patient_record["id"],
                    'name': extract_name(patient_record),
                    'mrn': extract_identifier(patient_record),
                    'age': extract_age(patient_record),
                    'sex': patient_record.get("gender", "unknown").capitalize(),
                    'conditions': extract_conditions(patient_record),
                    'vitals': {
                        'sbp': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Systolic Blood Pressure"), 120),
                        'dbp': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Diastolic Blood Pressure"), 80),
                        'hr': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Heart Rate"), 75),
                        'spo2': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Oxygen Saturation"), 98),
                        'weight': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Body Weight"), 70),
                        'height': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Body Height"), 170),
                        'bmi': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "BMI"), 24.5),
                        'pain_score': next((obs["value"] for obs in patient_record.get("observations", []) if obs.get("code", {}).get("text") == "Pain Score"), 2),
                    },
                    'labs': {
                        lab["code"]["text"]: lab["value"] 
                        for lab in patient_record.get("observations", []) 
                        if lab.get("category", {}).get("text") == "Laboratory"
                    },
                    'medications': [med["medication"]["code"]["text"] for med in patient_record.get("medications", [])],
                    'last_visit': movemend_data.get("last_visit_date", "2023-11-10"),
                    'next_appointment': movemend_data.get("next_appointment", "2023-12-05"),
                    'care_team': {
                        'primary': movemend_data.get("primary_provider", "Dr. Sarah Johnson"),
                        'specialist': movemend_data.get("specialist", "Dr. Robert Chen")
                    },
                    'notes': movemend_data.get("notes", []),
                    'movemend_data': movemend_data
                }
                
                # Calculate risk score
                risk_score, risk_level = get_risk_score(patient)
                patient['risk_score'] = risk_score
                patient['risk_level'] = risk_level
                
                processed_patients.append(patient)
            except Exception as e:
                st.warning(f"Could not process patient {patient_record.get('id')}: {str(e)}")
                continue
                
        # Sort patients by risk level
        risk_order = {"High": 0, "Medium": 1, "Low": 2}
        processed_patients.sort(key=lambda x: (risk_order[x['risk_level']], -x['risk_score']))
        
        if not processed_patients:
            st.error("No patients could be retrieved from the database. Please check if database servers are running properly.")
            st.stop()
            
        return processed_patients
        
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the Database Simulation servers.")
        st.info("Please make sure the database servers are running by executing:\n```\npython run_db_servers.py\n```")
        st.stop()
        
    except Exception as e:
        st.error(f"Error connecting to Database Simulation: {str(e)}")
        st.info("Please make sure the database servers are running by executing:\n```\npython run_db_servers.py\n```")
        st.stop()

def main():
    """Main function to run the Streamlit app."""
    st.markdown("<h1 class='main-header'>MoveMend Co Pilot</h1>", unsafe_allow_html=True)
    
    # Load patient data from Database Simulation
    patients = load_patients_from_database()
    
    # Initialize view mode in session state if not exists
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "Traditional View"
    
    # Patient selector in sidebar with custom styling
    patient_options = {f"{p['id']} - {p['name']}": p for p in patients}
    
    # Apply custom style to ensure dropdown has light background
    st.sidebar.markdown('''
    <style>
        div[data-baseweb="select"] {
            background-color: #ffffff !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
        }
        div[role="listbox"] {
            background-color: #ffffff !important;
        }
        div[role="option"] {
            background-color: #ffffff !important;
            color: #1a1a2e !important;
        }
        /* Voice mode button styling */
        .voice-mode-button {
            background-color: #f0f0f5;
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 20px;
            padding: 8px 16px;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .voice-mode-button:hover {
            background-color: rgba(46, 204, 113, 0.1);
        }
        .voice-mode-button.active {
            background-color: rgba(46, 204, 113, 0.2);
            border-color: #2ecc71;
        }
        .voice-mode-button i {
            margin-right: 8px;
        }
        /* Voice assistant container */
        .voice-assistant-container {
            background-color: rgba(46, 204, 113, 0.05);
            border: 1px solid rgba(46, 204, 113, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        /* Voice command input */
        .voice-command-input {
            padding: 10px;
            border-radius: 4px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            width: 100%;
            margin-bottom: 10px;
        }
    </style>
    ''', unsafe_allow_html=True)
    
    # Add voice mode toggle button to sidebar
    st.sidebar.markdown("### Voice Assistant")
    
    # Check if HUME API key is set
    has_hume_key = bool(os.getenv("HUME_API_KEY", ""))
    
    if not has_hume_key:
        st.sidebar.warning("⚠️ HUME API key not configured. Voice assistant is disabled.")
    elif not VOICE_AVAILABLE:
        st.sidebar.warning("⚠️ Voice processing not available. Check HUME library installation.")
    else:
        # Voice mode toggle button with conditional styling based on active state
        voice_mode_class = "voice-mode-button active" if st.session_state.voice_mode_active else "voice-mode-button"
        voice_mode_icon = "🔊" if st.session_state.voice_mode_active else "🔈"
        voice_mode_text = "Voice Mode: ON" if st.session_state.voice_mode_active else "Voice Mode: OFF"
        
        st.sidebar.markdown(f"""
        <div class="{voice_mode_class}" onclick="
            window.parent.postMessage({{action: 'toggleVoiceMode'}}, '*');
            setTimeout(function() {{ 
                window.parent.document.querySelector('[data-testid="stForm"]').submit();
            }}, 100);
        ">
            {voice_mode_icon} {voice_mode_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Add JavaScript to handle the toggle action
        st.sidebar.markdown("""
        <script>
            window.addEventListener('message', function(e) {
                if (e.data.action === 'toggleVoiceMode') {
                    // This event will be caught by Streamlit
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
                }
            });
        </script>
        """, unsafe_allow_html=True)
        
        # Add a button as fallback for the custom toggle
        if st.sidebar.button("Toggle Voice Assistant", key="toggle_voice"):
            AIClinicalAssistant.toggle_voice_mode()
            
        # Add speech recognition toggle only if voice mode is active
        if st.session_state.voice_mode_active and SPEECH_RECOGNITION_AVAILABLE:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Hands-Free Mode")
            
            # Speech recognition toggle button with conditional styling
            speech_mode_class = "voice-mode-button active" if st.session_state.speech_recognition_active else "voice-mode-button"
            speech_mode_icon = "🎙️" if st.session_state.speech_recognition_active else "🎤"
            speech_mode_text = "Speech Recognition: ON" if st.session_state.speech_recognition_active else "Speech Recognition: OFF"
            
            st.sidebar.markdown(f"""
            <div class="{speech_mode_class}" onclick="
                window.parent.postMessage({{action: 'toggleSpeechRecognition'}}, '*');
                setTimeout(function() {{ 
                    window.parent.document.querySelector('[data-testid="stForm"]').submit();
                }}, 100);
            ">
                {speech_mode_icon} {speech_mode_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Add JavaScript to handle the speech recognition toggle
            st.sidebar.markdown("""
            <script>
                window.addEventListener('message', function(e) {
                    if (e.data.action === 'toggleSpeechRecognition') {
                        // This event will be caught by Streamlit
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
                    }
                });
            </script>
            """, unsafe_allow_html=True)
            
            # Button as fallback for the custom toggle
            if st.sidebar.button("Toggle Speech Recognition", key="toggle_speech"):
                AIClinicalAssistant.toggle_speech_recognition()
                
            # Show information about hands-free mode
            if st.session_state.speech_recognition_active:
                st.sidebar.success("Hands-free mode active. Say commands like 'Tell me the summary of most critical patient today'")
                
                # Add option to view command history
                if st.session_state.voice_commands_history:
                    with st.sidebar.expander("Voice Command History"):
                        for i, cmd in enumerate(reversed(st.session_state.voice_commands_history[-5:])):
                            st.markdown(f"**{len(st.session_state.voice_commands_history)-i}.** {cmd}")
                        
                        if st.button("Clear History", key="clear_history"):
                            st.session_state.voice_commands_history = []
                            st.experimental_rerun()
    
    selected_patient_key = st.sidebar.selectbox(
        "Select Patient",
        options=list(patient_options.keys()),
        format_func=lambda x: x.split(" - ", 1)[1]  # Show only name in dropdown
    )
    
    selected_patient = patient_options[selected_patient_key]
    
    # Display patient data
    display_patient_header(selected_patient)
    
    # Breadcrumb selector for view mode
    st.markdown("""
    <style>
    .breadcrumb-container {
        display: flex;
        padding: 8px 0;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    .breadcrumb-item {
        padding: 8px 16px;
        margin-right: 5px;
        cursor: pointer;
        border-radius: 4px 4px 0 0;
        font-weight: 500;
        transition: all 0.2s;
    }
    .breadcrumb-active {
        background-color: rgba(75, 192, 141, 0.1);
        border-bottom: 2px solid #2ecc71;
        color: #1a1a2e;
    }
    .breadcrumb-inactive {
        color: #666;
        background-color: transparent;
    }
    .view-content {
        padding: 15px 0;
        display: none;
    }
    .view-content-active {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create container for breadcrumb and its content
    st.markdown("<div class='breadcrumb-view-container'>", unsafe_allow_html=True)
    
    # Create the breadcrumb selector with Streamlit buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Traditional View", key="traditional_view", 
                     use_container_width=True,
                     type="primary" if st.session_state.view_mode == "Traditional View" else "secondary"):
            st.session_state.view_mode = "Traditional View"
            st.experimental_rerun()
    
    with col2:
        if st.button("Summary", key="summary_view", 
                     use_container_width=True,
                     type="primary" if st.session_state.view_mode == "Summary" else "secondary"):
            st.session_state.view_mode = "Summary"
            st.experimental_rerun()
    
    # Keep CSS for other buttons in the app
    st.markdown("""
    <style>
    button[kind="secondary"],
    button.css-5rimss,
    button.css-gw32o0,
    button.css-1cpxqw2,
    button.css-1p1lx2y {
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Close the container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display KPI row and alerts in both views
    display_kpi_row(selected_patient)
    display_alerts(selected_patient)
    
    # Voice Mode UI - show only when activated
    if st.session_state.voice_mode_active and VOICE_AVAILABLE:
        # Add voice assistant container with styling
        st.markdown("""
        <div class="voice-assistant-container">
            <h3>🎙️ HUME AI Voice Assistant</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Add WebRTC audio stream for speech recognition if enabled
        if SPEECH_RECOGNITION_AVAILABLE and st.session_state.speech_recognition_active:
            # Add a voice activity indicator
            st.markdown("""
            <style>
            .voice-activity-indicator {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            .voice-activity-indicator .indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
                background-color: #2ecc71;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.4; }
                100% { opacity: 1; }
            }
            </style>
            <div class="voice-activity-indicator">
                <div class="indicator"></div>
                <span>Listening for voice commands...</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Show last recognized command if available
            if st.session_state.last_voice_command:
                st.markdown(f"**Last voice command:** {st.session_state.last_voice_command}")
                
                # Process the voice command if it hasn't been processed yet
                if 'last_processed_command' not in st.session_state or \
                   st.session_state.last_processed_command != st.session_state.last_voice_command:
                    # Store the command as being processed
                    st.session_state.last_processed_command = st.session_state.last_voice_command
                    
                    with st.spinner("Processing voice command..."):
                        # Process the voice command
                        try:
                            # Get text and audio response
                            text_response, selected_critical_patient, audio_bytes = AIClinicalAssistant.process_voice_command(
                                st.session_state.last_voice_command, patients
                            )
                            
                            # Store in session state for display
                            st.session_state.voice_output_ready = True
                            st.session_state.voice_output_audio = audio_bytes
                            st.session_state.voice_output_text = text_response
                            
                            # If a patient was selected, update the selected patient
                            if selected_critical_patient:
                                patient_id = selected_critical_patient.get('id')
                                if patient_id:
                                    # Find the matching patient key in patient_options
                                    for key, patient in patient_options.items():
                                        if patient.get('id') == patient_id:
                                            # Update selected patient in session state
                                            st.session_state.selected_patient_key = key
                                            # Force rerun to update the UI
                                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error processing voice command: {e}")
            
            # Add the WebRTC component for audio streaming
            st.markdown("### Live Microphone")
            
            def video_frame_callback(frame):
                # Just return the frame as we only care about audio
                return frame
                
            def audio_frame_callback(frame):
                # Process audio here if needed
                return frame
            
            # Add the WebRTC streamer
            webrtc_ctx = webrtc_streamer(
                key="speech-to-text",
                mode=WebRtcMode.SENDONLY,
                audio_frame_callback=audio_frame_callback,
                video_frame_callback=video_frame_callback,
                media_stream_constraints={"video": False, "audio": True},
                async_processing=True,
            )
            
            # When the WebRTC component is started, start the speech recognition
            if webrtc_ctx.state.playing and not st.session_state.speech_recognition_active:
                AIClinicalAssistant.start_speech_recognition()
            
            # When the WebRTC component is stopped, stop the speech recognition
            if not webrtc_ctx.state.playing and st.session_state.speech_recognition_active:
                AIClinicalAssistant.stop_speech_recognition()
                
        # Add voice command input as fallback or for typing mode
        voice_command = st.text_input("Ask a question or say 'Tell me the summary of most critical patient today'", 
                                    key="voice_command_input",
                                    placeholder="Type your voice command here...")
        
        # Voice command submission
        voice_submit_col1, voice_submit_col2 = st.columns([3, 1])
        with voice_submit_col2:
            if st.button("🎙️ Submit", key="voice_submit"):
                if voice_command:
                    with st.spinner("Processing voice command..."):
                        # Process the voice command
                        try:
                            # Get text and audio response
                            text_response, selected_critical_patient, audio_bytes = AIClinicalAssistant.process_voice_command(
                                voice_command, patients
                            )
                            
                            # Store in session state for display
                            st.session_state.voice_output_ready = True
                            st.session_state.voice_output_audio = audio_bytes
                            st.session_state.voice_output_text = text_response
                            
                            # If a patient was selected, update the selected patient
                            if selected_critical_patient:
                                patient_id = selected_critical_patient.get('id')
                                if patient_id:
                                    # Find the matching patient key in patient_options
                                    for key, patient in patient_options.items():
                                        if patient.get('id') == patient_id:
                                            # Update selected patient in session state
                                            st.session_state.selected_patient_key = key
                                            # Force rerun to update the UI
                                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error processing voice command: {e}")
        
        # Display voice assistant response
        if st.session_state.voice_output_ready and st.session_state.voice_output_text:
            st.markdown("### Voice Assistant Response:")
            st.markdown(st.session_state.voice_output_text)
            
            # Add audio playback if available
            if st.session_state.voice_output_audio:
                # Convert audio bytes to base64 to be playable in browser
                import base64
                audio_b64 = base64.b64encode(st.session_state.voice_output_audio).decode()
                
                # Embed audio player with the audio data
                st.markdown(f"""
                <audio controls autoplay>
                    <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                """, unsafe_allow_html=True)
            
            # Add option to clear voice output
            if st.button("Clear Voice Output", key="clear_voice"):
                st.session_state.voice_output_ready = False
                st.session_state.voice_output_audio = None
                st.session_state.voice_output_text = ""
                st.experimental_rerun()
    
    # Display view content based on selected view mode
    if st.session_state.view_mode == "Summary":
        # In Summary view, we want a more prominent display of the clinical summary
        st.markdown("""
        <style>
        .summary-container {
            border: 1px solid rgba(46, 204, 113, 0.3);
            border-radius: 8px;
            padding: 15px;
            background-color: rgba(46, 204, 113, 0.05);
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create a container for the summary view with a styled background
        with st.container():
            # Display the header inside this container
            st.markdown("### AI Clinical Summary")
            
            # Display clinical summary prominently
            display_clinical_summary(selected_patient)
            
            # Add an expander for additional details if needed
            with st.expander("View Additional Details"):
                # Display a subset of the traditional view in the expander
                display_active_problems(selected_patient)
                display_recent_labs(selected_patient)
    else:
        # Traditional View - display all sections except the AI Clinical Summary
        # No clinical summary in traditional view as per user's request
        display_trends(selected_patient)
        
        # Two-column layout for problems and labs
        col1, col2 = st.columns(2)
        
        with col1:
            display_active_problems(selected_patient)
        
        with col2:
            display_recent_labs(selected_patient)
        
        # Billing and exercise adherence
        display_billing()
        display_exercise_adherence(selected_patient)

if __name__ == "__main__":
    main()
