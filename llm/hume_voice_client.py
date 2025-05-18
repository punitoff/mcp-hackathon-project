"""HUME AI voice client for MoveMend copilot dashboard."""

import os
import json
import requests
import base64
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from hume import HumeClient
from hume.models.config import ProsodyConfig

# Import configuration
from llm.config import HUME_API_KEY, HUME_SECRET_KEY

class HumeVoiceClient:
    """Client for using HUME AI voice services with MoveMend dashboard."""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize the HUME AI client with the provided API key and secret key.
        
        Args:
            api_key: The Hume API key. If not provided, will use the HUME_API_KEY from config.
            secret_key: The Hume Secret key. If not provided, will use the HUME_SECRET_KEY from config.
        """
        self.api_key = api_key or HUME_API_KEY
        self.secret_key = secret_key or HUME_SECRET_KEY
        self.access_token = None
        
        # Initialize the client with the API key for backward compatibility
        # Token authentication will be used when needed
        self.client = HumeClient(self.api_key)
        
    def _get_access_token(self) -> str:
        """Get an access token using API key and Secret key.
        
        Returns:
            Access token string if successful, empty string otherwise.
        """
        try:
            # Create Basic auth credentials using API key as username and Secret key as password
            auth_string = f"{self.api_key}:{self.secret_key}"
            auth_bytes = auth_string.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            
            # Make the token request
            response = requests.post(
                "https://api.hume.ai/oauth2-cc/token",
                headers={
                    "Authorization": f"Basic {base64_auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data="grant_type=client_credentials"
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return self.access_token
            else:
                print(f"Error getting access token: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"Error authenticating with Hume API: {e}")
            return ""
        
    async def generate_voice_response(self, text: str, voice_id: str = "samantha") -> bytes:
        """Generate spoken voice audio from the provided text.
        
        Args:
            text: The text to convert to speech
            voice_id: The HUME voice ID to use (default: samantha)
            
        Returns:
            Audio bytes that can be played through a browser
        """
        # Configure the prosody (speech characteristics)
        config = ProsodyConfig(
            voice_id=voice_id,
            speed=1.0,              # Normal speaking speed
            pitch=0.0,              # Normal pitch
            prosody="conversational" # Conversational style for natural delivery
        )
        
        # Generate the voice response
        try:
            # Try to use token authentication if API and Secret keys are available
            if self.api_key and self.secret_key and not self.access_token:
                # Get an access token first
                self.access_token = self._get_access_token()
                
                # If token authentication failed, continue with API key
                if not self.access_token:
                    print("Token authentication failed, using API key authentication")
            
            # Generate the voice with the configured client
            response = await self.client.models.prosody.async_generate(
                text=text, 
                config=config
            )
            
            # Return the audio bytes
            return response.audio
        except Exception as e:
            print(f"Error generating voice response: {e}")
            # Try to refresh the token if authentication failed
            if "authentication" in str(e).lower() and self.api_key and self.secret_key:
                print("Trying to refresh access token and retry...")
                self.access_token = self._get_access_token()
                if self.access_token:
                    try:
                        # Retry with new token
                        response = await self.client.models.prosody.async_generate(
                            text=text, 
                            config=config
                        )
                        return response.audio
                    except Exception as retry_e:
                        print(f"Retry failed: {retry_e}")
            return None
            
    def generate_summary_voice(self, summary_text: str) -> bytes:
        """Generate a voice response for a clinical summary.
        
        This is a synchronous wrapper around the async method for easier integration.
        
        Args:
            summary_text: The clinical summary text to convert to speech
            
        Returns:
            Audio bytes that can be played through a browser
        """
        import asyncio
        
        # Create a new event loop if running in a synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async function and get the result
            audio_bytes = loop.run_until_complete(
                self.generate_voice_response(summary_text)
            )
            return audio_bytes
        finally:
            # Clean up the event loop
            loop.close()
    
    def get_critical_patient_summary_voice(self, patient_data: Dict) -> bytes:
        """Generate a voice response for the most critical patient summary.
        
        Args:
            patient_data: Patient data dictionary containing clinical information
            
        Returns:
            Audio bytes that can be played through a browser
        """
        # Create a focused critical summary for voice delivery
        summary_text = self._format_critical_patient_summary(patient_data)
        
        # Generate the voice response
        return self.generate_summary_voice(summary_text)
    
    def _format_critical_patient_summary(self, patient_data: Dict) -> str:
        """Format patient data into a concise critical summary for voice delivery.
        
        Args:
            patient_data: Patient data dictionary
            
        Returns:
            Formatted text optimized for voice delivery
        """
        # Extract key information
        name = patient_data.get("name", "Unknown patient")
        age = patient_data.get("age", "Unknown age")
        gender = patient_data.get("gender", "Unknown gender")
        
        # Get critical conditions
        conditions = patient_data.get("conditions", [])
        critical_conditions = [c for c in conditions if self._is_critical_condition(c)]
        
        # Get vital signs
        vitals = patient_data.get("vitals", {})
        
        # Get exercise adherence if available
        movemend_data = patient_data.get("movemend_data", {})
        adherence = movemend_data.get("adherence", "Unknown")
        
        # Build a voice-optimized summary
        summary = f"Critical summary for {name}, {age} year old {gender}. "
        
        if critical_conditions:
            summary += f"This patient has {len(critical_conditions)} critical conditions: {', '.join(critical_conditions)}. "
        else:
            summary += "This patient has no critical conditions at this time. "
        
        # Add vital signs if concerning
        if vitals:
            # Check for concerning vitals
            concerning_vitals = []
            
            sbp = vitals.get("sbp")
            dbp = vitals.get("dbp")
            if sbp and dbp and (sbp > 140 or dbp > 90 or sbp < 90 or dbp < 60):
                concerning_vitals.append(f"blood pressure is {sbp} over {dbp}")
                
            hr = vitals.get("hr")
            if hr and (hr > 100 or hr < 60):
                concerning_vitals.append(f"heart rate is {hr}")
            
            if concerning_vitals:
                summary += f"Concerning vital signs include: {', '.join(concerning_vitals)}. "
        
        # Add exercise adherence insights
        if adherence and adherence != "Unknown":
            if adherence < 50:
                summary += f"Exercise adherence is poor at {adherence}%. "
            elif adherence < 80:
                summary += f"Exercise adherence is moderate at {adherence}%. "
            else:
                summary += f"Exercise adherence is good at {adherence}%. "
        
        # Add recommendations
        summary += "Based on this assessment, I recommend: "
        
        if critical_conditions:
            summary += "immediate clinical review, "
        
        if vitals and any(v for v in concerning_vitals):
            summary += "monitoring of vital signs, "
        
        if adherence and adherence < 70:
            summary += "intervention to improve exercise adherence, "
        
        # Clean up the ending
        summary = summary.rstrip(", ") + "."
        
        return summary
    
    def _is_critical_condition(self, condition: str) -> bool:
        """Determine if a condition is considered critical.
        
        Args:
            condition: The medical condition to evaluate
            
        Returns:
            True if the condition is critical, False otherwise
        """
        # List of conditions considered critical
        critical_conditions = [
            "heart", "cardiac", "stroke", "pulmonary", "respiratory",
            "failure", "sepsis", "infection", "fracture", "trauma",
            "diabetes", "hypertension", "pain", "severe"
        ]
        
        # Check if any critical keyword is in the condition (case-insensitive)
        return any(keyword.lower() in condition.lower() for keyword in critical_conditions)

# Create a singleton instance with API key and secret key from config
hume_voice_client = HumeVoiceClient(HUME_API_KEY, HUME_SECRET_KEY)
