"""Configuration settings for LLM clients."""
import os

# Claude API key - loaded from environment variable
# For local development, set this in your .env file or export it in your terminal
# export ANTHROPIC_API_KEY="your-api-key-here"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Default model to use
CLAUDE_MODEL = "claude-3-opus-20240229"
