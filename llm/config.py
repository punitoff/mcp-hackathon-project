"""Configuration settings for LLM clients."""
import os

# API Keys and credentials
# For production, these should be set as environment variables

# Claude API configuration
# If not set in environment, we'll use the provided default value
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "HJ8LtlkWxj16nP4ZszOfhdUe5IHGGbXCW3rLUHwfTxALYV92")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")

# Hume API configuration
HUME_API_KEY = os.getenv("HUME_API_KEY", "HJ8LtlkWxj16nP4ZszOfhdUe5IHGGbXCW3rLUHwfTxALYV92")
HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY", "GvflD07WUydf0MMtVx5Lw7itAOo93eFkOyCbX1HjRwsw8vpTQ5rS7RsLkkQLgF6h")
