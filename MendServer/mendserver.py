from fastmcp import FastMCP
from anthropic import Anthropic
import os
import asyncio
from typing import AsyncIterator
from dotenv import load_dotenv 
load_dotenv()

# Create an MCP server
mcp = FastMCP("MendServer")
client = Anthropic()

@mcp.tool()
def analyze_json_batch(json_objects: list, analysis_prompt: str) -> list:
    """Analyze a batch of JSON objects using a single prompt template"""
    results = []
    for json_obj in json_objects:
        # Format the prompt template with the current JSON object
        formatted_prompt = analysis_prompt.format(json_data=json_obj)
        
        # Get analysis from Claude
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ]
        )
        results.append(message.content[0].text)
    return results

@mcp.resource("analysis-template/{template_id}")
def get_analysis_template(template_id: str) -> str:
    """Get a predefined analysis prompt template"""
    templates = {
        "medical": "Please analyze this medical record JSON: {json_data}",
        "billing": "Please extract billing information from: {json_data}",
        # Add more templates as needed
    }
    return templates.get(template_id, "Invalid template ID")

# Optional: Add a streaming version for real-time results
@mcp.tool()
async def analyze_json_stream(json_objects: list, analysis_prompt: str) -> AsyncIterator[str]:
    """Stream analysis results as they become available"""
    for json_obj in json_objects:
        formatted_prompt = analysis_prompt.format(json_data=json_obj)
        message = await client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ]
        )
        yield message.content[0].text

@mcp.tool()
def chat_with_llm(prompt: str) -> str:
    """Send a prompt to Claude and get a response"""
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",  # or another Claude model
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text

if __name__ == "__main__":
    # Start the server on localhost:8080 (default)
    mcp.run()
    
    # Or specify a different host and port:
    # mcp.run(host="0.0.0.0", port=9090)