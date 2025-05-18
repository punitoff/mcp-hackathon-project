"""Test script for Claude API integration."""

import os
from llm.claude_client import claude_client
from llm.config import CLAUDE_API_KEY

def test_claude_api():
    """Test basic Claude API functionality."""
    # Print API key information (masked for security)
    key_masked = "[None]" if not CLAUDE_API_KEY else f"{CLAUDE_API_KEY[:6]}...{CLAUDE_API_KEY[-4:]} (length: {len(CLAUDE_API_KEY)})"
    env_key_masked = "[None]" if not os.getenv("ANTHROPIC_API_KEY") else f"{os.getenv('ANTHROPIC_API_KEY')[:6]}...{os.getenv('ANTHROPIC_API_KEY')[-4:]} (length: {len(os.getenv('ANTHROPIC_API_KEY'))})"
    
    print(f"\nAPI key configuration:")
    print(f"- Config file API key: {key_masked}")
    print(f"- Environment API key: {env_key_masked}")
    print(f"- Using API key: {claude_client.api_key[:6]}...{claude_client.api_key[-4:]}")
    
    # Validate the API key
    print("\nValidating API key...")
    is_valid = claude_client.validate_api_key()
    
    if not is_valid:
        print("❌ API key validation failed. Check your API key and try again.")
        return False
    
    # Simple message to test the API
    print("\nAPI key is valid. Testing Claude API with a simple chat request...")
    messages = [
        {
            "role": "user",
            "content": "Hello, please respond with a brief greeting."
        }
    ]
    
    try:
        response = claude_client.chat(messages)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        print("\nResponse received:")
        print("-" * 60)
        print(text)
        print("-" * 60)
        print("✅ API test successful!")
        return True
    except Exception as e:
        print(f"\n❌ Error testing Claude API: {e}")
        return False

if __name__ == "__main__":
    test_claude_api()
