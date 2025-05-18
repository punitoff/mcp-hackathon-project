"""Base resources for the MCP server implementation."""

from typing import Dict, List, Any, Optional
import uuid
import base64

class Resource:
    """Base class for MCP resources."""
    
    def __init__(self, content: Any, resource_type: str, metadata: Optional[Dict[str, Any]] = None):
        self.uri = f"{resource_type}:{uuid.uuid4()}"
        self.content = content
        self.resource_type = resource_type
        self.metadata = metadata or {}
    
    def get_content(self) -> Any:
        """Get the resource content."""
        return self.content
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the resource metadata."""
        return self.metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the resource to a dictionary."""
        return {
            "uri": self.uri,
            "content": self.content,
            "resource_type": self.resource_type,
            "metadata": self.metadata
        }

class PatientResource(Resource):
    """Patient resource for the MCP server."""
    
    def __init__(self, patient_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        super().__init__(patient_data, "patient", metadata)
        # Set a custom URI that includes the patient ID for easier lookup
        if "id" in patient_data:
            self.uri = f"patient:{patient_data['id']}"

class MemoryResource(Resource):
    """Memory resource for storing contextual information in the MCP server."""
    
    def __init__(self, memory_data: Dict[str, Any], patient_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        # Generate metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add timestamp to metadata
        import datetime
        metadata["timestamp"] = datetime.datetime.now().isoformat()
        
        # Add patient ID to metadata if provided
        if patient_id:
            metadata["patient_id"] = patient_id
            # Set memory category from data if available
            memory_category = memory_data.get("category", "general")
            # Create URI with patient ID and timestamp for unique identification
            uri = f"memory:{patient_id}:{memory_category}:{metadata['timestamp']}"
            super().__init__(memory_data, "memory", metadata)
            self.uri = uri
        else:
            # For general (non-patient) memories
            memory_category = memory_data.get("category", "general")
            uri = f"memory:{memory_category}:{metadata['timestamp']}"
            super().__init__(memory_data, "memory", metadata)
            self.uri = uri

class VoiceResource(Resource):
    """Voice resource for text-to-speech content in the MCP server."""
    
    def __init__(self, voice_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        # Generate metadata if not provided
        if metadata is None:
            metadata = {}
            
        # Add timestamp and other voice metadata
        import datetime
        metadata["timestamp"] = datetime.datetime.now().isoformat()
        
        # Add voice specific metadata
        if "voice_id" in voice_data:
            metadata["voice_id"] = voice_data["voice_id"]
        
        # Create a unique URI for this voice resource
        text_preview = voice_data.get("text", "")[:20].replace(" ", "_")
        uri = f"voice:{text_preview}:{metadata['timestamp']}"
        
        # Initialize the resource
        super().__init__(voice_data, "voice", metadata)
        self.uri = uri
        
    def get_audio_base64(self) -> str:
        """Get the base64 encoded audio content."""
        audio_bytes = self.content.get("audio_bytes")
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return ""

class ResourceRegistry:
    """Registry of MCP resources."""
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
    
    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the registry."""
        self.resources[resource.uri] = resource
    
    def get_resource(self, uri: str) -> Optional[Resource]:
        """Get a resource by URI."""
        return self.resources.get(uri)
    
    def list_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all resources or resources of a specific type."""
        resources = self.resources.values()
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return [{
            "uri": r.uri,
            "resource_type": r.resource_type,
            "metadata": r.metadata
        } for r in resources]
