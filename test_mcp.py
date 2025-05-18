#!/usr/bin/env python
"""Simple test script for the MCP server."""

import os
import sys
import json

# Make sure the project directories are in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the MCP server
from mcp_server.app import mcp_server

def test_mcp_server():
    """Test the MCP server by initializing it and listing resources."""
    print("Testing MCP Server...")
    
    # Initialize the MCP server
    print("\nInitializing MCP server...")
    mcp_server.initialize()
    print("MCP server initialized!")
    
    # List resources
    print("\nListing resources:")
    resources, next_cursor = mcp_server.list_resources()
    print(f"Found {len(resources)} resources. Next cursor: {next_cursor}")
    
    # Print each resource
    for i, resource in enumerate(resources):
        print(f"\nResource {i+1}:")
        print(f"  URI: {resource.get('uri')}")
        print(f"  Type: {resource.get('resource_type')}")
        print(f"  Metadata: {json.dumps(resource.get('metadata', {}), indent=2)}")
    
    # If we have resources, try reading the first one
    if resources:
        uri = resources[0]['uri']
        print(f"\nReading resource {uri}...")
        resource_content = mcp_server.read_resource(uri)
        if resource_content:
            print(f"Successfully read resource: {resource_content.get('resource_type')}")
            # Just show a sample of the content to avoid too much output
            content_sample = str(resource_content.get('content'))[:200] + "..." if len(str(resource_content.get('content'))) > 200 else str(resource_content.get('content'))
            print(f"Content sample: {content_sample}")
        else:
            print(f"Failed to read resource {uri}")
    
    print("\nMCP Server test complete!")

if __name__ == "__main__":
    test_mcp_server()
