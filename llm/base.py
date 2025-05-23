# automated_skeptic_mvp/llm/base.py
"""
LLM Abstraction Layer - Unified interface for different LLM providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import logging

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"  # For Gemini
    HUGGINGFACE = "huggingface"
    LOCAL = "local"

@dataclass
class LLMMessage:
    """Standardized message format for LLM interactions"""
    role: str  # system, user, assistant
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMResponse:
    """Standardized response format from LLM providers"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, Any]] = None  # tokens, cost, etc.
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    additional_params: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize the provider-specific client"""
        pass
    
    @abstractmethod
    def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate response from messages"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "available": self.is_available()
        }