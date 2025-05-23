# automated_skeptic_mvp/llm/providers/ollama_provider.py
"""
Ollama LLM Provider - Local LLM integration
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from ..base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider

class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local LLM inference"""
    
    def _initialize(self):
        """Initialize Ollama client"""
        self.base_url = self.config.base_url or "http://localhost:11434"
        self.api_url = f"{self.base_url}/api"
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self._available = response.status_code == 200
            
            if self._available:
                # Check if model is available
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.config.model not in model_names:
                    self.logger.warning(f"Model {self.config.model} not found in Ollama. Available models: {model_names}")
                    # Try to pull the model
                    self._pull_model()
                
        except Exception as e:
            self.logger.warning(f"Ollama not available: {str(e)}")
            self._available = False
    
    def _pull_model(self) -> bool:
        """Pull model if not available"""
        try:
            self.logger.info(f"Attempting to pull model: {self.config.model}")
            
            pull_data = {"name": self.config.model, "stream": False}
            response = requests.post(
                f"{self.api_url}/pull",
                json=pull_data,
                timeout=300  # 5 minutes for model download
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully pulled model: {self.config.model}")
                return True
            else:
                self.logger.error(f"Failed to pull model: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error pulling model: {str(e)}")
            return False
    
    def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate response using Ollama"""
        if not self.is_available():
            raise RuntimeError("Ollama provider is not available")
        
        # Convert messages to Ollama format
        prompt = self._format_messages(messages)
        
        # Prepare request data
        request_data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        # Add any additional parameters
        if self.config.additional_params:
            request_data["options"].update(self.config.additional_params)
        
        # Remove None values
        request_data["options"] = {k: v for k, v in request_data["options"].items() if v is not None}
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/generate",
                json=request_data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            processing_time = time.time() - start_time
            
            return LLMResponse(
                content=result.get("response", ""),
                provider=LLMProvider.OLLAMA,
                model=self.config.model,
                usage={
                    "processing_time": processing_time,
                    "total_tokens": result.get("eval_count", 0),
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                },
                metadata={
                    "done": result.get("done", False),
                    "context": result.get("context"),
                }
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama API error: {str(e)}")
            raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format messages for Ollama (simple concatenation for now)"""
        formatted_parts = []
        
        for message in messages:
            if message.role == "system":
                formatted_parts.append(f"System: {message.content}")
            elif message.role == "user":
                formatted_parts.append(f"Human: {message.content}")
            elif message.role == "assistant":
                formatted_parts.append(f"Assistant: {message.content}")
        
        formatted_parts.append("Assistant:")
        return "\n\n".join(formatted_parts)
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        return getattr(self, '_available', False)
    
    def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except Exception as e:
            self.logger.error(f"Error listing models: {str(e)}")
        
        return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model"""
        model_name = model_name or self.config.model
        
        try:
            response = requests.post(
                f"{self.api_url}/show",
                json={"name": model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error getting model info: {str(e)}")
        
        return {}