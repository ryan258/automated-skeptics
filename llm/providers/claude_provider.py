# automated_skeptic_mvp/llm/providers/claude_provider.py
"""
Claude/Anthropic LLM Provider - External API integration
"""

import time
from typing import List, Dict, Any, Optional
from ..base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class ClaudeProvider(BaseLLMProvider):
    """Claude/Anthropic provider for external LLM inference"""
    
    def _initialize(self):
        """Initialize Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            self.logger.warning("Anthropic package not installed. Install with: pip install anthropic")
            self._available = False
            return
            
        if not self.config.api_key:
            self.logger.warning("Anthropic API key not provided")
            self._available = False
            return
        
        try:
            # Initialize the Anthropic client
            self.client = anthropic.Anthropic(api_key=self.config.api_key)
            
            # Test API availability (Claude doesn't have a list models endpoint, so we'll mark as available)
            self._available = True
            self.logger.info("Claude client initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Claude API not available: {str(e)}")
            self._available = False
    
    def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate response using Claude API"""
        if not self.is_available():
            raise RuntimeError("Claude provider is not available")
        
        # Separate system message from user messages for Claude
        system_content = ""
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                user_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # If no user messages, create one
        if not user_messages:
            user_messages = [{"role": "user", "content": "Please respond."}]
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model,
            "messages": user_messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
        }
        
        # Add system message if present
        if system_content:
            request_params["system"] = system_content
        
        # Add max_tokens if specified
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        else:
            # Claude requires max_tokens, so set a default
            request_params["max_tokens"] = 1000
        
        # Add additional parameters if provided
        if self.config.additional_params:
            request_params.update(self.config.additional_params)
        
        # Remove None values
        request_params = {k: v for k, v in request_params.items() if v is not None}
        
        try:
            start_time = time.time()
            
            # Use the Anthropic client
            response = self.client.messages.create(**request_params)
            
            processing_time = time.time() - start_time
            
            # Extract content from response
            content = ""
            if response.content and len(response.content) > 0:
                # Claude returns content as a list of content blocks
                if hasattr(response.content[0], 'text'):
                    content = response.content[0].text
                else:
                    content = str(response.content[0])
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.config.model,
                usage={
                    "processing_time": processing_time,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "estimated_cost": self._calculate_cost(response.usage)
                },
                metadata={
                    "stop_reason": response.stop_reason,
                    "response_id": response.id,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Claude API error: {str(e)}")
            raise RuntimeError(f"Claude generation failed: {str(e)}")
    
    def _calculate_cost(self, usage) -> float:
        """Calculate estimated cost based on token usage"""
        # Claude pricing (as of 2024)
        cost_per_1k_tokens = {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-2.1": {"input": 0.008, "output": 0.024},
            "claude-2.0": {"input": 0.008, "output": 0.024},
        }
        
        model_costs = cost_per_1k_tokens.get(self.config.model, {"input": 0.003, "output": 0.015})
        
        input_cost = (usage.input_tokens / 1000) * model_costs["input"]
        output_cost = (usage.output_tokens / 1000) * model_costs["output"]
        
        return round(input_cost + output_cost, 6)
    
    def is_available(self) -> bool:
        """Check if Claude API is available"""
        return getattr(self, '_available', False)
    
    def list_models(self) -> List[str]:
        """List available Claude models"""
        # Claude doesn't have a models endpoint, so return known models
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620", 
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]
