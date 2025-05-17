from fastmcp import FastMCP
from anthropic import Anthropic
import os
from dotenv import load_dotenv  # You'll need to pip install python-dotenv
load_dotenv()

# Create an MCP server
mcp = FastMCP("MendServer")
client = Anthropic()

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

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Start the server on localhost:8080 (default)
    mcp.run()
    
    # Or specify a different host and port:
    # mcp.run(host="0.0.0.0", port=9090)