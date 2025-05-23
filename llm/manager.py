# automated_skeptic_mvp/llm/manager.py
"""
LLM Manager - Coordinates multiple LLM providers and handles routing
"""

import logging
from typing import List, Dict, Any, Optional, Union
from .base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.ollama_provider import OllamaProvider

class LLMManager:
    """Manages multiple LLM providers and routes requests"""
    
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured LLM providers"""
        # Get LLM configurations from settings
        llm_configs = self._load_llm_configs()
        
        for provider_name, config in llm_configs.items():
            try:
                provider = self._create_provider(config)
                if provider and provider.is_available():
                    self.providers[provider_name] = provider
                    self.logger.info(f"Initialized LLM provider: {provider_name} ({config.model})")
                else:
                    self.logger.warning(f"Provider {provider_name} not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize provider {provider_name}: {str(e)}")
    
    def _load_llm_configs(self) -> Dict[str, LLMConfig]:
        """Load LLM configurations from settings"""
        configs = {}
        
        # OpenAI configuration
        openai_key = self.settings.get('API_KEYS', 'openai_api_key')
        if openai_key:
            configs['openai_default'] = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=self.settings.get('LLM_MODELS', 'openai_model', 'gpt-3.5-turbo'),
                api_key=openai_key,
                temperature=self.settings.getfloat('LLM_MODELS', 'openai_temperature', 0.1),
                max_tokens=self.settings.getint('LLM_MODELS', 'openai_max_tokens', 500)
            )
        
        # Ollama configuration
        ollama_enabled = self.settings.get('LLM_MODELS', 'ollama_enabled', 'true').lower() == 'true'
        if ollama_enabled:
            configs['ollama_default'] = LLMConfig(
                provider=LLMProvider.OLLAMA,
                model=self.settings.get('LLM_MODELS', 'ollama_model', 'llama2'),
                base_url=self.settings.get('LLM_MODELS', 'ollama_base_url', 'http://localhost:11434'),
                temperature=self.settings.getfloat('LLM_MODELS', 'ollama_temperature', 0.1),
                max_tokens=self.settings.getint('LLM_MODELS', 'ollama_max_tokens', 500)
            )
        
        # Agent-specific configurations
        for agent_name in ['herald', 'illuminator', 'logician', 'seeker', 'oracle']:
            agent_provider = self.settings.get('AGENT_LLM_MAPPING', f'{agent_name}_llm', '')
            if agent_provider:
                # Create agent-specific config based on base provider
                base_config_name = f"{agent_provider}_default"
                if base_config_name in configs:
                    base_config = configs[base_config_name]
                    configs[f'{agent_name}_llm'] = LLMConfig(
                        provider=base_config.provider,
                        model=self.settings.get('AGENT_LLM_MAPPING', f'{agent_name}_model', base_config.model),
                        api_key=base_config.api_key,
                        base_url=base_config.base_url,
                        temperature=self.settings.getfloat('AGENT_LLM_MAPPING', f'{agent_name}_temperature', base_config.temperature),
                        max_tokens=self.settings.getint('AGENT_LLM_MAPPING', f'{agent_name}_max_tokens', base_config.max_tokens)
                    )
        
        return configs
    
    def _create_provider(self, config: LLMConfig) -> Optional[BaseLLMProvider]:
        """Create a provider instance based on configuration"""
        if config.provider == LLMProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == LLMProvider.OLLAMA:
            return OllamaProvider(config)
        # Add more providers here as needed
        else:
            self.logger.error(f"Unsupported provider: {config.provider}")
            return None
    
    def generate(
        self, 
        messages: Union[List[LLMMessage], str], 
        agent_name: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using specified or default provider"""
        
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [LLMMessage(role="user", content=messages)]
        
        # Determine which provider to use
        selected_provider = self._select_provider(agent_name, provider_name)
        
        if not selected_provider:
            raise RuntimeError("No available LLM provider found")
        
        try:
            return selected_provider.generate(messages, **kwargs)
        except Exception as e:
            # Try fallback provider
            fallback_provider = self._get_fallback_provider(selected_provider)
            if fallback_provider:
                self.logger.warning(f"Primary provider failed, trying fallback: {str(e)}")
                return fallback_provider.generate(messages, **kwargs)
            else:
                raise
    
    def _select_provider(self, agent_name: Optional[str], provider_name: Optional[str]) -> Optional[BaseLLMProvider]:
        """Select appropriate provider based on agent and preferences"""
        
        # 1. Use explicitly specified provider
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        
        # 2. Use agent-specific provider
        if agent_name:
            agent_provider_name = f"{agent_name}_llm"
            if agent_provider_name in self.providers:
                return self.providers[agent_provider_name]
        
        # 3. Use default providers in order of preference
        preference_order = ['ollama_default', 'openai_default']
        for provider_name in preference_order:
            if provider_name in self.providers:
                return self.providers[provider_name]
        
        return None
    
    def _get_fallback_provider(self, failed_provider: BaseLLMProvider) -> Optional[BaseLLMProvider]:
        """Get fallback provider when primary fails"""
        # If OpenAI fails, try Ollama
        if failed_provider.config.provider == LLMProvider.OPENAI:
            return self.providers.get('ollama_default')
        
        # If Ollama fails, try OpenAI
        elif failed_provider.config.provider == LLMProvider.OLLAMA:
            return self.providers.get('openai_default')
        
        return None
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available providers"""
        return {
            name: provider.get_provider_info() 
            for name, provider in self.providers.items()
        }
    
    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a specific provider is available"""
        provider = self.providers.get(provider_name)
        return provider is not None and provider.is_available()
    
    def get_provider_for_agent(self, agent_name: str) -> Optional[str]:
        """Get the provider name configured for a specific agent"""
        agent_provider_name = f"{agent_name}_llm"
        if agent_provider_name in self.providers:
            return agent_provider_name
        
        # Return default if no specific mapping
        for provider_name in ['ollama_default', 'openai_default']:
            if provider_name in self.providers:
                return provider_name
        
        return None
    
    def estimate_cost(self, text: str, provider_name: Optional[str] = None) -> float:
        """Estimate cost for processing text with given provider"""
        # Simple token estimation (rough approximation)
        estimated_tokens = len(text.split()) * 1.3  # Average tokens per word
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            if provider.config.provider == LLMProvider.OPENAI:
                # Use OpenAI pricing
                return (estimated_tokens / 1000) * 0.002  # Rough estimate
            else:
                # Local models are essentially free
                return 0.0
        
        return 0.0  # Default to free if unknown