# automated_skeptic_mvp/llm/providers/openai_provider.py
"""
OpenAI LLM Provider - External API integration (Updated for OpenAI v1.0+)
"""

import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider

class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for external LLM inference (Updated for v1.0+)"""
    
    def _initialize(self):
        """Initialize OpenAI client"""
        if not self.config.api_key:
            self.logger.warning("OpenAI API key not provided")
            self._available = False
            return
        
        try:
            # Initialize the new OpenAI client
            self.client = OpenAI(api_key=self.config.api_key)
            
            # Test API availability with a minimal request
            models = self.client.models.list()
            self._available = True
            self.logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"OpenAI API not available: {str(e)}")
            self._available = False
    
    def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API"""
        if not self.is_available():
            raise RuntimeError("OpenAI provider is not available")
        
        # Convert to OpenAI message format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
        }
        
        # Add max_tokens if specified
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        # Add additional parameters if provided
        if self.config.additional_params:
            request_params.update(self.config.additional_params)
        
        # Remove None values
        request_params = {k: v for k, v in request_params.items() if v is not None}
        
        try:
            start_time = time.time()
            
            # Use the new client interface
            response = self.client.chat.completions.create(**request_params)
            
            processing_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider.OPENAI,
                model=self.config.model,
                usage={
                    "processing_time": processing_time,
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "estimated_cost": self._calculate_cost(response.usage)
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id,
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
    
    def _calculate_cost(self, usage) -> float:
        """Calculate estimated cost based on token usage"""
        # Updated cost calculation for current OpenAI pricing (2024)
        cost_per_1k_tokens = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        }
        
        model_costs = cost_per_1k_tokens.get(self.config.model, {"input": 0.002, "output": 0.002})
        
        input_cost = (usage.prompt_tokens / 1000) * model_costs["input"]
        output_cost = (usage.completion_tokens / 1000) * model_costs["output"]
        
        return round(input_cost + output_cost, 6)
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        return getattr(self, '_available', False)
    
    def list_models(self) -> List[str]:
        """List available OpenAI models"""
        try:
            if not self.is_available():
                return []
            
            models = self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id]
        except Exception as e:
            self.logger.error(f"Error listing OpenAI models: {str(e)}")
            return []
