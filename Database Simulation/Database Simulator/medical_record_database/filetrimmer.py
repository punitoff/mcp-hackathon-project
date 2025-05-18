import json
from datetime import datetime
from collections import defaultdict
import os

def trim_fhir_file(input_path, output_path):
    # Read the JSON file
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Dictionary to store latest report for each test type
    latest_reports = defaultdict(lambda: {'datetime': datetime.min.replace(tzinfo=None), 'report': None})
    
    # Process each entry
    for entry in data.get('entry', []):
        resource = entry.get('resource', {})
        
        # Skip if not a DiagnosticReport
        if resource.get('resourceType') != 'DiagnosticReport':
            continue
            
        # Get the test type from the code display
        test_type = None
        coding = resource.get('code', {}).get('coding', [])
        if coding:
            test_type = coding[0].get('display')
        
        if not test_type:
            continue
            
        # Get the datetime
        dt_str = resource.get('effectiveDateTime')
        if not dt_str:
            continue
            
        # Parse datetime and ensure it's timezone naive
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            dt = dt.replace(tzinfo=None)  # Convert to naive datetime
        except ValueError:
            continue
            
        # Update if this is the latest for this test type
        if dt > latest_reports[test_type]['datetime']:
            latest_reports[test_type] = {
                'datetime': dt,
                'report': entry
            }
    
    # Create new trimmed bundle
    trimmed_data = {
        'resourceType': 'Bundle',
        'entry': [report['report'] for report in latest_reports.values()]
    }
    
    # Write trimmed data to output file
    with open(output_path, 'w') as f:
        json.dump(trimmed_data, f, indent=2)
    
    # Print summary
    print(f"Original number of entries: {len(data.get('entry', []))}")
    print(f"Trimmed number of entries: {len(trimmed_data['entry'])}")
    print("\nUnique test types preserved:")
    for test_type in sorted(latest_reports.keys()):
        dt = latest_reports[test_type]['datetime']
        print(f"- {test_type} (latest: {dt.strftime('%Y-%m-%d %H:%M:%S')})")

# Get input and output directories
input_dir = "synthea_sample_data_fhir_latest"
output_dir = "trimmed_database"

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Process each file in input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename)
        print(f"\nProcessing {filename}...")
        try:
            trim_fhir_file(input_file, output_file)
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")