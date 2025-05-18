#!/usr/bin/env python
"""Example of using MCP memory with Claude for clinical summaries."""

import os
import sys
from pprint import pprint

# Make sure the project directories are in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the necessary components
from mcp_server.app import mcp_server
from llm.claude_mcp_client import claude_mcp_client

def generate_memory_enhanced_summary():
    """Generate a clinical summary that incorporates MCP memories."""
    print("Generating memory-enhanced clinical summary...")
    
    # Initialize the MCP server
    print("\nInitializing MCP server...")
    mcp_server.initialize()
    print("MCP server initialized!")
    
    # Get a patient to work with
    print("\nGetting a patient to work with...")
    resources, _ = mcp_server.list_resources("patient")
    if not resources:
        print("No patient resources found!")
        return
        
    patient_uri = resources[0]["uri"]
    patient_id = patient_uri.split(":")[-1]
    print(f"Using patient: {patient_uri}")
    
    # Create some memories for this patient
    print("\nCreating patient memories...")
    mcp_server.create_memory(
        "Patient mentioned experiencing increased shoulder pain after gardening last weekend.",
        "clinical_observation",
        patient_id
    )
    
    mcp_server.create_memory(
        "Patient prefers afternoon appointments and responds well to hands-on techniques.",
        "patient_preference",
        patient_id
    )
    
    mcp_server.create_memory(
        "Patient has been inconsistent with home exercise program - needs simplified routine.",
        "treatment_insight",
        patient_id
    )
    
    # Generate a system prompt that instructs Claude to use memories
    system_prompt = """You are an AI clinical assistant for MoveMend physical therapy.
When generating summaries:
1. Use the MCP system to retrieve patient data
2. Check for stored memories about the patient using the get_memories tool
3. Incorporate relevant memories into your assessment and recommendations
4. Be concise but comprehensive
5. Use proper medical terminology while remaining clear
"""

    # Generate a clinical summary using Claude with MCP
    print("\nGenerating clinical summary with memory integration...")
    summary = claude_mcp_client.generate_clinical_summary_with_mcp(
        patient_uri=patient_uri,
        system_prompt=system_prompt
    )
    
    print("\n=== MEMORY-ENHANCED CLINICAL SUMMARY ===")
    print(summary)
    print("========================================")

if __name__ == "__main__":
    # Make sure ANTHROPIC_API_KEY is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set!")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)
        
    generate_memory_enhanced_summary()
