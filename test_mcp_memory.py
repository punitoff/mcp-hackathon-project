#!/usr/bin/env python
"""Test script for the MCP memory functionality."""

import os
import sys
import json
from pprint import pprint

# Make sure the project directories are in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the MCP server
from mcp_server.app import mcp_server

def test_mcp_memory():
    """Test the MCP memory system."""
    print("Testing MCP Memory System...")
    
    # Initialize the MCP server
    print("\nInitializing MCP server...")
    mcp_server.initialize()
    print("MCP server initialized!")
    
    # Get a patient ID to use for memories
    print("\nGetting a patient ID...")
    resources, _ = mcp_server.list_resources("patient")
    if not resources:
        print("No patient resources found!")
        return
        
    patient_id = resources[0]["uri"].split(":")[-1]
    print(f"Using patient ID: {patient_id}")
    
    # Create a clinical memory
    print("\nCreating a clinical insight memory...")
    clinical_memory = mcp_server.create_memory(
        "Patient shows improved range of motion in left shoulder after 3 weeks of therapy.",
        "clinical_insight",
        patient_id
    )
    print(f"Created memory: {clinical_memory}")
    
    # Create a patient preference memory
    print("\nCreating a patient preference memory...")
    pref_memory = mcp_server.create_memory(
        "Patient prefers morning appointments and responds well to visual exercise guides.",
        "patient_preference",
        patient_id
    )
    print(f"Created memory: {pref_memory}")
    
    # Create a general memory (not tied to patient)
    print("\nCreating a general memory...")
    general_memory = mcp_server.create_memory(
        "MoveMend clinic will be closed for holidays from Dec 24-26.",
        "general_info",
        None
    )
    print(f"Created memory: {general_memory}")
    
    # Retrieve all memories for the patient
    print(f"\nRetrieving all memories for patient {patient_id}...")
    patient_memories = mcp_server.get_memories(patient_id=patient_id)
    print(f"Found {len(patient_memories)} patient memories:")
    for i, memory in enumerate(patient_memories):
        print(f"\nMemory {i+1}:")
        print(f"  URI: {memory.get('resource_type')}:{memory.get('uri')}")
        print(f"  Content: {memory.get('content', {}).get('content')}")
        print(f"  Category: {memory.get('content', {}).get('category')}")
    
    # Retrieve all memories by category
    print(f"\nRetrieving all clinical insight memories...")
    clinical_memories = mcp_server.get_memories(category="clinical_insight")
    print(f"Found {len(clinical_memories)} clinical insight memories:")
    for i, memory in enumerate(clinical_memories):
        print(f"\nMemory {i+1}:")
        print(f"  URI: {memory.get('uri')}")
        print(f"  Content: {memory.get('content', {}).get('content')}")
        
    # Delete a memory
    if patient_memories:
        memory_to_delete = patient_memories[0]["uri"]
        print(f"\nDeleting memory {memory_to_delete}...")
        delete_result = mcp_server.delete_memory(memory_to_delete)
        print(f"Delete result: {delete_result}")
        
        # Verify deletion
        updated_memories = mcp_server.get_memories(patient_id=patient_id)
        print(f"Patient now has {len(updated_memories)} memories after deletion")
    
    print("\nMCP Memory test complete!")

if __name__ == "__main__":
    test_mcp_memory()
