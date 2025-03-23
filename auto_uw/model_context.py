"""
Protocol for model context interactions.
"""

from typing import Protocol, Dict, Any, List, Optional
from datetime import datetime

class ModelContext(Protocol):
    """Protocol defining the interface for model context interactions."""
    def get_system_prompt(self) -> str:
        """Get the system prompt for the model."""
        ...
    
    def format_user_prompt(self, content: str) -> Dict[str, str]:
        """Format user content into a model-compatible prompt."""
        ...
    
    def parse_model_response(self, response: Any) -> Dict[str, Any]:
        """Parse the model's response into a structured format."""
        ...
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle and format model errors."""
        ...
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get model-specific parameters (temperature, max_tokens, etc.)."""
        ...
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate the model's response against expected schema."""
        ...
    
    def get_context_window(self) -> int:
        """Get the model's context window size."""
        ...
    
    def get_token_count(self, text: str) -> int:
        """Estimate the token count for a given text."""
        ... 