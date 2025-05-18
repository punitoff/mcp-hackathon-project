"""Thin wrapper around OpenAI ChatCompletion API with function calling support."""
import os
from typing import List, Dict, Any, Union, Optional

import openai

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

openai.api_key = os.getenv("OPENAI_API_KEY", "")


async def chat_async(messages: List[Dict[str, str]], functions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    response = await openai.ChatCompletion.acreate(
        model=OPENAI_MODEL,
        messages=messages,
        functions=functions or [],
    )
    return response.choices[0].to_dict()
