# automated_skeptic_mvp/llm/providers/gemini_provider.py
"""
Gemini/Google AI LLM Provider - External API integration
"""

import time
from typing import List, Dict, Any, Optional
from ..base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

class GeminiProvider(BaseLLMProvider):
    """Gemini/Google AI provider for external LLM inference"""
    
    def _initialize(self):
        """Initialize Google AI client"""
        if not GOOGLE_AI_AVAILABLE:
            self.logger.warning("Google AI package not installed. Install with: pip install google-generativeai")
            self._available = False
            return
            
        if not self.config.api_key:
            self.logger.warning("Google AI API key not provided")
            self._available = False
            return
        
        try:
            # Configure the API key
            genai.configure(api_key=self.config.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.config.model)
            
            # Test API availability by listing models
            models = genai.list_models()
            self._available = True
            self.logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Gemini API not available: {str(e)}")
            self._available = False
    
    def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini API"""
        if not self.is_available():
            raise RuntimeError("Gemini provider is not available")
        
        # Convert messages to Gemini format
        # Gemini prefers a single prompt, so we'll combine messages
        prompt_parts = []
        
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System instructions: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        # Add final prompt for assistant response
        prompt_parts.append("Assistant:")
        full_prompt = "\n\n".join(prompt_parts)
        
        # Prepare generation config
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get('temperature', self.config.temperature),
            max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
        )
        
        # Add additional parameters if provided
        if self.config.additional_params:
            for key, value in self.config.additional_params.items():
                if hasattr(generation_config, key):
                    setattr(generation_config, key, value)
        
        try:
            start_time = time.time()
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            
            # Extract content
            content = ""
            if response.text:
                content = response.text
            
            # Calculate token usage (Gemini API provides token counts)
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                total_tokens = prompt_tokens + completion_tokens
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.GOOGLE,
                model=self.config.model,
                usage={
                    "processing_time": processing_time,
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "estimated_cost": self._calculate_cost(prompt_tokens, completion_tokens)
                },
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "unknown",
                    "safety_ratings": [rating.category.name + ":" + rating.probability.name 
                                     for rating in response.candidates[0].safety_ratings] if response.candidates else [],
                }
            )
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            raise RuntimeError(f"Gemini generation failed: {str(e)}")
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost based on token usage"""
        # Gemini pricing (as of 2024)
        cost_per_1k_tokens = {
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
            "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},  # Legacy name
        }
        
        model_costs = cost_per_1k_tokens.get(self.config.model, {"input": 0.0005, "output": 0.0015})
        
        input_cost = (prompt_tokens / 1000) * model_costs["input"]
        output_cost = (completion_tokens / 1000) * model_costs["output"]
        
        return round(input_cost + output_cost, 6)
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return getattr(self, '_available', False)
    
    def list_models(self) -> List[str]:
        """List available Gemini models"""
        try:
            if not self.is_available():
                return []
            
            models = genai.list_models()
            model_names = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    # Extract model name from full path
                    model_name = model.name.split('/')[-1]
                    model_names.append(model_name)
            
            return model_names
        except Exception as e:
            self.logger.error(f"Error listing Gemini models: {str(e)}")
            return [
                "gemini-1.5-pro",
                "gemini-1.5-flash", 
                "gemini-1.0-pro",
                "gemini-pro"
            ]
