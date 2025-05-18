# Clinical Copilot Dashboard

A Streamlit-based dashboard for clinicians to monitor patient vitals, trends, and alerts.

## Features

- Patient overview with key vitals and alerts
- Interactive trend visualizations for cardiometabolic data, weight/BMI, and mood
- Active problems and recent lab results
- Color-coded KPIs for quick assessment
- Responsive design for different screen sizes

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-hackathon-project
   ```

2. Navigate to the dashboard directory:
   ```bash
   cd dashboard
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

1. Start the Streamlit application:
   ```bash
   streamlit run clinical_copilot.py
   ```

2. The dashboard will open automatically in your default web browser. If it doesn't, navigate to:
   ```
   http://localhost:8501
   ```

## Usage

- Use the sidebar to select different patients
- View color-coded KPIs for quick assessment
- Navigate between different trend tabs to see historical data
- Check the alerts section for important notifications
- View active problems and recent lab results

## File Structure

```
dashboard/
├── clinical_copilot.py     # Main Streamlit application
├── requirements.txt         # Python dependencies
└── data/                    # Patient data directory
    └── patient_1.json       # Example patient data (if available)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
