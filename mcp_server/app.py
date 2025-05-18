"""MCP server implementation for MoveMend hackathon project."""

import sys
import os
import datetime
from typing import Dict, List, Any, Optional, Tuple
import json

# Add Database Simulation directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Database Simulation'))
from client_medicaldataretrieval import get_random_patient_data, get_movemend_data

from .resources import Resource, PatientResource, MemoryResource, ResourceRegistry

class MCPServer:
    """MCP server implementation that works with Streamlit."""
    
    def __init__(self):
        self.registry = ResourceRegistry()
        self.server_name = "movemend-mcp-server"
        self.initialized = False
    
    def initialize(self):
        """Initialize the MCP server with data from the simulated databases."""
        if self.initialized:
            return
        
        # Get random patients from the medical records database
        try:
            records = get_random_patient_data(10)
            records_json = records.json()
            
            # Add each patient as a resource
            for record in records_json:
                # Get MoveMend data for this patient
                record["movemend_data"] = get_movemend_data(record["id"]).json()
                
                # Create metadata for easier discovery
                metadata = {
                    "name": record.get("name", "Unknown"),
                    "gender": record.get("gender", "Unknown"),
                    "age": record.get("age", 0),
                    "conditions_count": len(record.get("conditions", [])),
                    "has_movemend_data": "movemend_data" in record and bool(record["movemend_data"])
                }
                
                # Create and register the patient resource
                patient_resource = PatientResource(record, metadata)
                self.registry.add_resource(patient_resource)
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing MCP server: {e}")
            return False
    
    def list_resources(self, resource_type: Optional[str] = None, cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """List resources, optionally filtered by type."""
        resources = self.registry.list_resources(resource_type)
        
        # Simple pagination (not really needed for our small dataset)
        if cursor:
            try:
                start_idx = int(cursor)
                page_size = 10
                end_idx = start_idx + page_size
                result_page = resources[start_idx:end_idx]
                next_cursor = str(end_idx) if end_idx < len(resources) else None
                return result_page, next_cursor
            except ValueError:
                # Invalid cursor, return first page
                return resources[:10], "10" if len(resources) > 10 else None
        else:
            # No cursor, return first page
            return resources[:10], "10" if len(resources) > 10 else None
    
    def read_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """Read a resource by URI."""
        resource = self.registry.get_resource(uri)
        if resource:
            return resource.to_dict()
        return None
        
    def create_memory(self, content: str, category: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new memory resource.
        
        Args:
            content: The content of the memory to store
            category: The category of the memory (e.g., clinical_insight, observation)
            patient_id: Optional patient ID to associate the memory with
            
        Returns:
            Dictionary with the URI of the created memory resource
        """
        # Create the memory data
        memory_data = {
            "content": content,
            "category": category,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Create the memory resource
        memory_resource = MemoryResource(memory_data, patient_id)
        
        # Add it to the registry
        self.registry.add_resource(memory_resource)
        
        return {"memory_uri": memory_resource.uri, "status": "created"}
    
    def get_memories(self, patient_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memories, optionally filtered by patient ID and/or category.
        
        Args:
            patient_id: Optional patient ID to filter by
            category: Optional category to filter by
            
        Returns:
            List of memory resources matching the criteria
        """
        # List all memory resources
        all_resources = self.registry.list_resources("memory")
        
        # Filter by criteria if provided
        filtered_resources = []
        for resource in all_resources:
            # Get the full resource to access metadata
            full_resource = self.registry.get_resource(resource["uri"])
            if not full_resource:
                continue
                
            metadata = full_resource.get_metadata()
            
            # Check if patient ID matches (if provided)
            if patient_id and metadata.get("patient_id") != patient_id:
                continue
                
            # Check if category matches (if provided)
            if category and full_resource.get_content().get("category") != category:
                continue
                
            # All filters passed, add to result
            filtered_resources.append(full_resource.to_dict())
        
        # Sort by timestamp (newest first)
        filtered_resources.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        
        return filtered_resources
    
    def delete_memory(self, memory_uri: str) -> bool:
        """Delete a memory by URI.
        
        Args:
            memory_uri: The URI of the memory to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        # Check if the memory exists
        resource = self.registry.get_resource(memory_uri)
        if not resource or resource.resource_type != "memory":
            return False
            
        # Remove from registry
        self.registry.resources.pop(memory_uri, None)
        
        return True

# Create a singleton instance
mcp_server = MCPServer()
