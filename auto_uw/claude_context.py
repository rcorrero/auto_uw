"""
Claude-specific implementation of the ModelContext protocol.
"""

from typing import Dict, Any, Optional
from .model_context import ModelContext
import json

class ClaudeContext(ModelContext):
    """Implementation of ModelContext for Claude model."""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        self.model = model
        self._system_prompt = """
        You are an expert insurance underwriter for small business policies. Your task is to:
        
        1. Analyze the provided business information
        2. Identify relevant risk factors
        3. Apply underwriting guidelines from the provided document excerpts
        4. Calculate an appropriate premium estimate
        
        Be thorough in your risk assessment and strictly adhere to all regulatory requirements.
        """
    
    def get_system_prompt(self) -> str:
        return self._system_prompt
    
    def format_user_prompt(self, content: str) -> Dict[str, str]:
        return {
            "role": "user",
            "content": content
        }
    
    def parse_model_response(self, response: Any) -> Dict[str, Any]:
        """Parse Claude's response into a structured format."""
        try:
            # Extract the text content from Claude's response
            content = response.content[0].text
            
            # Try to find and parse JSON in the response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return {"parsed": True, "data": json.loads(json_str)}
            else:
                return {"parsed": False, "raw_content": content}
        except Exception as e:
            return self.handle_error(e)
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        return {
            "error": str(error),
            "error_type": type(error).__name__,
            "parsed": False
        }
    
    def get_model_parameters(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95
        }
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate the model's response against expected schema."""
        if "error" in response:
            return False
        return True
    
    def get_context_window(self) -> int:
        """Get Claude's context window size."""
        # Claude 3 Sonnet has a 200K token context window
        return 200000
    
    def get_token_count(self, text: str) -> int:
        """Estimate the token count for a given text."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4 