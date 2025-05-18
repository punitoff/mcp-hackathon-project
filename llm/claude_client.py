"""Anthropic Claude API client with MCP support for MoveMend project."""

import os
import json
from typing import Dict, List, Any, Optional, Union
import anthropic
# Use the compatible imports based on the installed version
try:
    from anthropic.types import ContentBlock, MessageParam
except ImportError:
    # Fallback to direct dictionary structures for older versions
    ContentBlock = dict
    MessageParam = dict

# Import configuration settings
from .config import CLAUDE_API_KEY, CLAUDE_MODEL

class ClaudeClient:
    """Client for Anthropic's Claude API with MCP support."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Priority: 1. Passed API key, 2. Hardcoded API key, 3. Environment variable
        self.api_key = api_key or CLAUDE_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = CLAUDE_MODEL
        
    def validate_api_key(self) -> bool:
        """Check if the API key is valid by making a minimal API call."""
        if not self.api_key or len(self.api_key) < 10:  # Basic length check
            return False
            
        try:
            # Simple API call to validate the key
            response = self.chat(
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10  # Minimal token count to save costs
            )
            # If we get here without an exception, the key is valid
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False
    
    async def chat_async(self, messages: List[Dict[str, str]], 
                        system_prompt: Optional[str] = None, 
                        tools: Optional[List[Dict[str, Any]]] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 1000) -> Dict[str, Any]:
        """Send a chat request to Claude asynchronously."""
        
        try:
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Create kwargs for the API call
            kwargs = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Only add system and tools if they are provided and not None
            if system_prompt is not None:
                kwargs["system"] = system_prompt
                
            # Don't include tools parameter if not needed or not supported
            if tools and hasattr(self.client.messages, "create") and "tools" in self.client.messages.create.__code__.co_varnames:
                kwargs["tools"] = tools
            
            # Make the API call
            response = await self.client.messages.create(**kwargs)
            
            # Handle response conversion
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            elif hasattr(response, 'dict'):
                return response.dict()
            else:
                return response
        except Exception as e:
            print(f"Error in async Claude API call: {e}")
            # Return a simple error response
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error calling Claude API asynchronously: {str(e)}"
                }]
            }

    def chat(self, messages: List[Dict[str, str]], 
            system_prompt: Optional[str] = None, 
            tools: Optional[List[Dict[str, Any]]] = None,
            temperature: float = 0.7,
            max_tokens: int = 1000) -> Dict[str, Any]:
        """Send a chat request to Claude synchronously."""
        
        try:
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Create kwargs for the API call
            kwargs = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Only add system and tools if they are provided and not None
            if system_prompt is not None:
                kwargs["system"] = system_prompt
                
            # Don't include tools parameter if not needed or not supported
            if tools and hasattr(self.client.messages, "create") and "tools" in self.client.messages.create.__code__.co_varnames:
                kwargs["tools"] = tools
            
            # Make the API call
            response = self.client.messages.create(**kwargs)
            
            # Handle response conversion
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            elif hasattr(response, 'dict'):
                return response.dict()
            else:
                return response
        except Exception as e:
            print(f"Error in Claude API call: {e}")
            # Return a simple error response
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error calling Claude API: {str(e)}"
                }]
            }
    
    def generate_clinical_summary(self, patient_data: Dict[str, Any], 
                                 system_prompt: Optional[str] = None,
                                 temperature: float = 0.3) -> str:
        """Generate a clinical summary for a patient."""
        
        if system_prompt is None:
            system_prompt = """You are a clinical assistant helping physical therapists review patient data.
Create a concise morning brief summary that highlights:
1. Key patient demographics and conditions
2. Recent vital signs and their trends
3. Progress in therapy
4. Any concerning patterns or alerts
5. Suggested next steps or focus areas

Be brief but thorough, focusing on clinically relevant information. Use clear headings and bullet points."""
        
        messages = [{
            "role": "user",
            "content": f"Generate a clinical summary for this patient data: {json.dumps(patient_data, indent=2)}"
        }]
        
        response = self.chat(messages, system_prompt, temperature=temperature, max_tokens=1500)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        return text
    
    def generate_clinical_insights(self, patient_data: Dict[str, Any],
                                  additional_question: Optional[str] = None,
                                  system_prompt: Optional[str] = None,
                                  temperature: float = 0.3) -> str:
        """Generate clinical insights and analysis for a patient."""
        
        if system_prompt is None:
            system_prompt = """You are an experienced clinical assistant with expertise in physical therapy.
Analyze the patient data and provide:
1. Key insights about the patient's condition and progress
2. Potential areas of concern or improvement
3. Evidence-based recommendations
4. Specific rehabilitation strategies that might be beneficial

Base your analysis on clinical best practices and the available patient data. 
Be precise and actionable in your recommendations."""
        
        prompt = f"Analyze this patient's data and provide clinical insights: {json.dumps(patient_data, indent=2)}"
        if additional_question:
            prompt += f"\n\nSpecifically address this question: {additional_question}"
            
        messages = [{
            "role": "user",
            "content": prompt
        }]
        
        response = self.chat(messages, system_prompt, temperature=temperature, max_tokens=1500)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        return text
    
    def generate_soap_note(self, patient_data: Dict[str, Any],
                          system_prompt: Optional[str] = None,
                          temperature: float = 0.3) -> str:
        """Generate a SOAP note for a patient visit."""
        
        if system_prompt is None:
            system_prompt = """You are a physical therapy clinical assistant.
Generate a comprehensive SOAP note based on the patient data provided:
- Subjective: Summarize the patient's reported symptoms, concerns and progress
- Objective: Document measurable findings including vitals, range of motion, strength, etc.
- Assessment: Evaluate the patient's overall status, progress towards goals, and any new findings
- Plan: Recommend next steps in treatment, any adjustments needed, and follow-up timeline

Use professional medical terminology and be concise but thorough."""
        
        messages = [{
            "role": "user",
            "content": f"Generate a SOAP note for this patient's latest visit: {json.dumps(patient_data, indent=2)}"
        }]
        
        response = self.chat(messages, system_prompt, temperature=temperature, max_tokens=1500)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        return text

# Create a singleton instance
claude_client = ClaudeClient()
