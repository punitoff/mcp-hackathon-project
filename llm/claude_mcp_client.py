"""Claude MCP client that connects Claude to the MCP server."""

import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import anthropic
# Use the compatible imports based on the installed version
try:
    from anthropic.types import ContentBlock, MessageParam, Tool, ToolParam
except ImportError:
    # Fallback to direct dictionary structures for older versions
    ContentBlock = dict
    MessageParam = dict
    Tool = dict
    ToolParam = dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server.app import mcp_server
from llm.config import CLAUDE_API_KEY, CLAUDE_MODEL

class ClaudeMCPClient:
    """Client for using Claude with MCP for MoveMend."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or CLAUDE_API_KEY
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = CLAUDE_MODEL
        
        # Define MCP tools
        self.mcp_tools = self._create_mcp_tools()
    
    def _create_mcp_tools(self) -> List[Dict[str, Any]]:
        """Create MCP tools for Claude."""
        return [
            {
                "name": "list_resources",
                "description": "Lists the available resources from the MCP server.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "description": "Optional type of resource to filter by (e.g., 'patient', 'memory')."
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for getting the next page of results."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "read_resource",
                "description": "Reads the content of a specific resource by URI.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "uri": {
                            "type": "string",
                            "description": "URI of the resource to read."
                        }
                    },
                    "required": ["uri"]
                }
            },
            {
                "name": "generate_voice",
                "description": "Generates speech audio from text using Hume AI voice synthesis.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to convert to speech."
                        },
                        "voice_id": {
                            "type": "string",
                            "description": "Optional voice ID to use (default: samantha)."
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "create_memory",
                "description": "Creates a new memory entry in the MCP server.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content of the memory to store."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category of the memory (e.g., 'clinical_insight', 'patient_preference', 'observation')."
                        },
                        "patient_id": {
                            "type": "string",
                            "description": "Optional patient ID to associate this memory with."
                        }
                    },
                    "required": ["content", "category"]
                }
            },
            {
                "name": "get_memories",
                "description": "Retrieves memories from the MCP server with optional filters.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Optional patient ID to filter memories by."
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category to filter memories by."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "delete_memory",
                "description": "Deletes a memory from the MCP server by URI.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "memory_uri": {
                            "type": "string",
                            "description": "URI of the memory to delete."
                        }
                    },
                    "required": ["memory_uri"]
                }
            }
        ]
    
    def _handle_tool_calls(self, tool_calls) -> List[Dict]:
        """Handle tool calls from Claude."""
        # Make sure MCP server is initialized
        from mcp_server.app import mcp_server
        if not mcp_server.initialized:
            mcp_server.initialize()
            
        tool_results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("input", {})
            
            if tool_name == "list_resources":
                result = self._handle_list_resources(tool_args)
            elif tool_name == "read_resource":
                result = self._handle_read_resource(tool_args)
            elif tool_name == "create_memory":
                result = self._handle_create_memory(tool_args)
            elif tool_name == "get_memories":
                result = self._handle_get_memories(tool_args)
            elif tool_name == "delete_memory":
                result = self._handle_delete_memory(tool_args)
            elif tool_name == "generate_voice":
                result = self._handle_generate_voice(tool_args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
                
            tool_results.append({
                "tool_call_id": tool_call.get("id"),
                "output": json.dumps(result)
            })
            
        return tool_results
    
    def _handle_mcp_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP tool call from Claude."""
        try:
            tool_name = tool_call.get("name")
            tool_params = tool_call.get("parameters", {})
            
            # Initialize MCP server if not already initialized
            if not mcp_server.initialized:
                mcp_server.initialize()
            
            if tool_name == "list_resources":
                resource_type = tool_params.get("resource_type")
                cursor = tool_params.get("cursor")
                resources, next_cursor = mcp_server.list_resources(resource_type, cursor)
                return {
                    "resources": resources,
                    "next_cursor": next_cursor
                }
            elif tool_name == "read_resource":
                uri = tool_params.get("uri")
                if not uri:
                    return {"error": "URI is required"}
                resource = mcp_server.read_resource(uri)
                if not resource:
                    return {"error": f"Resource not found: {uri}"}
                return resource
            elif tool_name == "create_memory":
                content = tool_params.get("content")
                category = tool_params.get("category")
                patient_id = tool_params.get("patient_id")
                memory = mcp_server.create_memory(content, category, patient_id)
                return memory
            elif tool_name == "get_memories":
                patient_id = tool_params.get("patient_id")
                category = tool_params.get("category")
                memories = mcp_server.get_memories(patient_id, category)
                return memories
            elif tool_name == "delete_memory":
                memory_uri = tool_params.get("memory_uri")
                if not memory_uri:
                    return {"error": "Memory URI is required"}
                result = mcp_server.delete_memory(memory_uri)
                return result
            elif tool_name == "generate_voice":
                text = tool_params.get("text")
                voice_id = tool_params.get("voice_id", "samantha")
                if not text:
                    return {"error": "Missing required 'text' parameter"}
                result = mcp_server.generate_voice(text, voice_id)
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_list_resources(self, tool_args):
        resource_type = tool_args.get("resource_type")
        cursor = tool_args.get("cursor")
        resources, next_cursor = mcp_server.list_resources(resource_type, cursor)
        return {
            "resources": resources,
            "next_cursor": next_cursor
        }
    
    def _handle_read_resource(self, tool_args):
        uri = tool_args.get("uri")
        if not uri:
            return {"error": "URI is required"}
        resource = mcp_server.read_resource(uri)
        if not resource:
            return {"error": f"Resource not found: {uri}"}
        return resource
    
    def _handle_create_memory(self, tool_args):
        content = tool_args.get("content")
        category = tool_args.get("category")
        patient_id = tool_args.get("patient_id")
        memory = mcp_server.create_memory(content, category, patient_id)
        return memory
    
    def _handle_get_memories(self, tool_args):
        patient_id = tool_args.get("patient_id")
        category = tool_args.get("category")
        memories = mcp_server.get_memories(patient_id, category)
        return memories
    
    def _handle_delete_memory(self, tool_args):
        """Handle the delete_memory tool call."""
        memory_uri = tool_args.get("memory_uri")
        if memory_uri:
            result = mcp_server.delete_memory(memory_uri)
            return {"content": [{"type": "text", "text": json.dumps({"success": result})}]}
            
        return {"content": [{"type": "text", "text": "Error: Missing memory_uri parameter"}]}
        
    def _handle_generate_voice(self, tool_args):
        """Handle the generate_voice tool call."""
        text = tool_args.get("text")
        voice_id = tool_args.get("voice_id", "samantha")
        
        if not text:
            return {"content": [{"type": "text", "text": "Error: Missing required 'text' parameter"}]}
            
        # Generate voice using MCP server
        result = mcp_server.generate_voice(text, voice_id)
        
        # Return the result as a pretty-printed JSON string
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    
    def chat_with_mcp(self, messages: List[Dict[str, str]], 
                     system_prompt: Optional[str] = None,
                     temperature: float = 0.7,
                     max_tokens: int = 1000) -> Dict[str, Any]:
        """Send a chat request to Claude with MCP tools enabled."""
        
        try:
            # Simplified implementation that uses direct text rather than tool calls
            # This is a fallback for older versions of the Anthropic SDK that don't support tools
            
            # Format messages for the Anthropic API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Create system prompt that includes instructions for MCP
            enhanced_system_prompt = system_prompt or ""
            enhanced_system_prompt += """
\nYou have access to patient data through an MCP server. To access this data, describe what you need in your response, and I will fetch it for you.

You can:
1. List available patient resources by asking for a list of patients
2. Read a specific patient's data by asking for the patient by ID

Explain what information you need, and I'll provide it in a follow-up message.
"""
            
            # Create the initial response
            response = self.client.messages.create(
                model=self.model,
                messages=formatted_messages,
                system=enhanced_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Convert the response to a dictionary
            # Handle both object with model_dump() method and direct dictionaries
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            elif hasattr(response, 'dict'):
                return response.dict()
            else:
                return response
                
        except Exception as e:
            print(f"Error in chat_with_mcp: {e}")
            # Return a simple error response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Could not process MCP request: {str(e)}"
                    }
                ]
            }
    
    def generate_clinical_summary_with_mcp(self, patient_uri: Optional[str] = None,
                                         system_prompt: Optional[str] = None,
                                         temperature: float = 0.3) -> str:
        """Generate a clinical summary using MCP to fetch patient data."""
        
        if system_prompt is None:
            system_prompt = """You are a clinical assistant helping physical therapists review patient data.
You have access to patient data through MCP. Follow these steps:
1. List available patient resources using the list_resources tool with resource_type="patient"
2. If a specific patient URI is provided, read that resource
3. If no URI is provided, choose a patient and read their data
4. Generate a concise clinical summary with these sections:
   - Patient Overview: demographics and conditions
   - Recent Vitals: latest measurements and trends
   - Therapy Progress: based on MoveMend data
   - Clinical Alerts: any concerning patterns
   - Recommendations: suggested next steps

Be brief but thorough, focusing on clinically relevant information."""
        
        # Initial message
        if patient_uri:
            initial_message = f"Generate a clinical summary for the patient with URI: {patient_uri}"
        else:
            initial_message = "Generate a clinical summary for a patient. First, list available patients using MCP."
        
        messages = [{
            "role": "user",
            "content": initial_message
        }]
        
        # Get response with MCP
        response = self.chat_with_mcp(messages, system_prompt, temperature=temperature, max_tokens=2000)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        return text
    
    def answer_clinical_question_with_mcp(self, question: str,
                                        patient_uri: Optional[str] = None,
                                        system_prompt: Optional[str] = None,
                                        temperature: float = 0.3) -> str:
        """Answer a clinical question using MCP to access patient data."""
        
        if system_prompt is None:
            system_prompt = """You are an expert clinical assistant helping physical therapists.
You have access to patient data through MCP tools. When answering clinical questions:
1. First, determine if you need patient data to answer the question
2. If needed, list patient resources and read the relevant patient data
3. Base your answer on the patient's specific information and clinical best practices
4. Be clear, concise, and clinically precise in your response
5. When appropriate, provide evidence-based recommendations

Always prioritize patient safety and clinical accuracy in your responses."""
        
        # Initial message
        if patient_uri:
            initial_message = f"Answer this clinical question about the patient with URI {patient_uri}: {question}"
        else:
            initial_message = f"Answer this clinical question: {question} First, determine if you need to access patient data using MCP."
        
        messages = [{
            "role": "user",
            "content": initial_message
        }]
        
        # Get response with MCP
        response = self.chat_with_mcp(messages, system_prompt, temperature=temperature, max_tokens=2000)
        
        # Extract the text from the response
        text = ""
        for content in response.get("content", []):
            if content.get("type") == "text":
                text += content.get("text", "")
        
        return text

# Create a singleton instance
claude_mcp_client = ClaudeMCPClient()
