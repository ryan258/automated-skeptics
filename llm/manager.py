# automated_skeptic_mvp/llm/manager.py
"""
LLM Manager - Coordinates multiple LLM providers with bias detection
Updated for Phase 6
"""

import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from .base import BaseLLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.ollama_provider import OllamaProvider

# Import new providers with fallback
try:
    from .providers.claude_provider import ClaudeProvider
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from .providers.gemini_provider import GeminiProvider
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LLMManager:
    """Manages multiple LLM providers and routes requests with bias awareness"""
    
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.providers: Dict[str, BaseLLMProvider] = {}
        
        # Performance tracking
        self.provider_performance = {}
        
        # Bias patterns
        self.bias_patterns = {
            'political_sensitive': [
                'berlin wall', 'tiananmen square', 'hong kong protests', 'taiwan',
                'tibet', 'xinjiang', 'uyghur', 'democracy china', 'human rights china'
            ],
            'safe_providers': ['claude', 'openai', 'gemini'],
            'risky_providers': ['deepseek', 'qwen', 'baichuan']
        }
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured LLM providers"""
        llm_configs = self._load_llm_configs()
        
        for provider_name, config in llm_configs.items():
            try:
                provider = self._create_provider(config)
                if provider and provider.is_available():
                    self.providers[provider_name] = provider
                    self.provider_performance[provider_name] = {
                        'total_requests': 0,
                        'success_rate': 1.0,
                        'avg_response_time': 0.0,
                        'bias_incidents': 0
                    }
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
                model=self.settings.get('LLM_MODELS', 'openai_model', 'gpt-4o-mini'),
                api_key=openai_key,
                temperature=self.settings.getfloat('LLM_MODELS', 'openai_temperature', 0.1),
                max_tokens=self.settings.getint('LLM_MODELS', 'openai_max_tokens', 500)
            )
        
        # Claude/Anthropic configuration
        claude_key = self.settings.get('API_KEYS', 'anthropic_api_key')
        if claude_key and CLAUDE_AVAILABLE:
            configs['claude_default'] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model=self.settings.get('LLM_MODELS', 'claude_model', 'claude-3-5-sonnet-20241022'),
                api_key=claude_key,
                temperature=self.settings.getfloat('LLM_MODELS', 'claude_temperature', 0.1),
                max_tokens=self.settings.getint('LLM_MODELS', 'claude_max_tokens', 500)
            )
        
        # Gemini/Google AI configuration
        gemini_key = self.settings.get('API_KEYS', 'google_ai_api_key')
        if gemini_key and GEMINI_AVAILABLE:
            configs['gemini_default'] = LLMConfig(
                provider=LLMProvider.GOOGLE,
                model=self.settings.get('LLM_MODELS', 'gemini_model', 'gemini-1.5-flash'),
                api_key=gemini_key,
                temperature=self.settings.getfloat('LLM_MODELS', 'gemini_temperature', 0.1),
                max_tokens=self.settings.getint('LLM_MODELS', 'gemini_max_tokens', 500)
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
        elif config.provider == LLMProvider.ANTHROPIC and CLAUDE_AVAILABLE:
            return ClaudeProvider(config)
        elif config.provider == LLMProvider.GOOGLE and GEMINI_AVAILABLE:
            return GeminiProvider(config)
        else:
            self.logger.error(f"Unsupported or unavailable provider: {config.provider}")
            return None
    
    def generate(
        self, 
        messages: Union[List[LLMMessage], str], 
        agent_name: Optional[str] = None,
        provider_name: Optional[str] = None,
        content_context: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response with bias-aware provider selection"""
        
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [LLMMessage(role="user", content=messages)]
        
        # Check for bias risk
        content = self._extract_content_for_analysis(messages, content_context)
        bias_risk = self._assess_bias_risk(content)
        
        # Select provider based on bias risk
        selected_provider = self._select_bias_aware_provider(
            agent_name, provider_name, bias_risk
        )
        
        if not selected_provider:
            raise RuntimeError("No suitable LLM provider found")
        
        try:
            response = selected_provider.generate(messages, **kwargs)
            
            # Add bias metadata
            response.metadata = response.metadata or {}
            response.metadata.update({
                'bias_risk_score': bias_risk,
                'provider_selected_for_bias': bias_risk > 0.3
            })
            
            # Update performance metrics
            self._update_provider_metrics(selected_provider, bias_risk)
            
            return response
            
        except Exception as e:
            # Try fallback provider
            fallback_provider = self._get_fallback_provider(selected_provider, bias_risk)
            if fallback_provider:
                self.logger.warning(f"Primary provider failed, trying fallback: {str(e)}")
                return fallback_provider.generate(messages, **kwargs)
            else:
                raise
    
    def generate_ensemble(
        self,
        messages: Union[List[LLMMessage], str],
        providers: Optional[List[str]] = None,
        voting_method: str = 'weighted',
        **kwargs
    ) -> LLMResponse:
        """Generate response using ensemble of multiple providers"""
        
        if isinstance(messages, str):
            messages = [LLMMessage(role="user", content=messages)]
        
        # Select providers for ensemble
        if not providers:
            providers = self._select_ensemble_providers()
        
        responses = []
        errors = []
        
        # Get responses from multiple providers
        for provider_name in providers:
            if provider_name in self.providers:
                try:
                    response = self.providers[provider_name].generate(messages, **kwargs)
                    responses.append((provider_name, response))
                except Exception as e:
                    errors.append((provider_name, str(e)))
                    self.logger.warning(f"Ensemble provider {provider_name} failed: {str(e)}")
        
        if not responses:
            raise RuntimeError(f"All ensemble providers failed: {errors}")
        
        # Return best response based on voting method
        if voting_method == 'weighted':
            return self._weighted_ensemble_response(responses)
        else:
            # Return best single response
            return max(responses, key=lambda x: self._score_response(x[1]))[1]
    
    def _extract_content_for_analysis(
        self, 
        messages: List[LLMMessage], 
        context: Optional[str]
    ) -> str:
        """Extract content for bias analysis"""
        content_parts = []
        
        for msg in messages:
            content_parts.append(msg.content)
        
        if context:
            content_parts.append(context)
        
        return " ".join(content_parts)
    
    def _assess_bias_risk(self, content: str) -> float:
        """Assess bias risk in content"""
        content_lower = content.lower()
        
        # Check for politically sensitive keywords
        sensitive_matches = 0
        for keyword in self.bias_patterns['political_sensitive']:
            if keyword in content_lower:
                sensitive_matches += 1
        
        # Calculate risk score
        if sensitive_matches == 0:
            return 0.0
        
        # High risk patterns
        high_risk_patterns = [
            'berlin wall.*1989', 'tiananmen.*1989', 'hong kong.*protest'
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, content_lower):
                return 0.8
        
        # Base risk from keyword matches
        risk_score = min(sensitive_matches * 0.3, 0.7)
        
        return risk_score
    
    def _select_bias_aware_provider(
        self, 
        agent_name: Optional[str], 
        provider_name: Optional[str],
        bias_risk: float
    ) -> Optional[BaseLLMProvider]:
        """Select provider considering bias risk"""
        
        # If low bias risk, use normal selection
        if bias_risk < 0.3:
            return self._select_provider(agent_name, provider_name)
        
        # High bias risk - prioritize safe providers
        safe_providers = ['claude_default', 'openai_default', 'gemini_default']
        available_safe_providers = [
            name for name in safe_providers 
            if name in self.providers
        ]
        
        if available_safe_providers:
            # Select best performing safe provider
            return self.providers[available_safe_providers[0]]
        
        # Fallback to normal selection
        return self._select_provider(agent_name, provider_name)
    
    def _select_provider(self, agent_name: Optional[str], provider_name: Optional[str]) -> Optional[BaseLLMProvider]:
        """Select appropriate provider (original logic)"""
        
        # 1. Use explicitly specified provider
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        
        # 2. Use agent-specific provider
        if agent_name:
            agent_provider_name = f"{agent_name}_llm"
            if agent_provider_name in self.providers:
                return self.providers[agent_provider_name]
        
        # 3. Use default providers in order of preference
        preference_order = [
            'ollama_default',    # Local first (free)
            'claude_default',    # High quality
            'gemini_default',    # Good balance
            'openai_default'     # Reliable fallback
        ]
        
        for provider_name in preference_order:
            if provider_name in self.providers:
                return self.providers[provider_name]
        
        return None
    
    def _get_fallback_provider(
        self, 
        failed_provider: BaseLLMProvider, 
        bias_risk: float
    ) -> Optional[BaseLLMProvider]:
        """Get fallback provider when primary fails"""
        failed_provider_type = failed_provider.config.provider
        
        # For high bias risk, prefer safe providers
        if bias_risk > 0.5:
            safe_fallbacks = ['claude_default', 'openai_default', 'gemini_default']
            for provider_name in safe_fallbacks:
                if (provider_name in self.providers and 
                    self.providers[provider_name].config.provider != failed_provider_type):
                    return self.providers[provider_name]
        
        # Normal fallback logic
        fallback_order = [
            'ollama_default',
            'claude_default', 
            'gemini_default',
            'openai_default'
        ]
        
        for provider_name in fallback_order:
            if (provider_name in self.providers and 
                self.providers[provider_name].config.provider != failed_provider_type):
                return self.providers[provider_name]
        
        return None
    
    def _select_ensemble_providers(self) -> List[str]:
        """Select providers for ensemble voting"""
        # Use up to 3 providers from different types
        provider_types = {}
        for name, provider in self.providers.items():
            provider_type = provider.config.provider.value
            if provider_type not in provider_types:
                provider_types[provider_type] = []
            provider_types[provider_type].append(name)
        
        ensemble_providers = []
        for provider_type, providers in provider_types.items():
            if providers:
                ensemble_providers.append(providers[0])  # Take first of each type
        
        return ensemble_providers[:3]  # Limit to 3 for cost control
    
    def _weighted_ensemble_response(self, responses: List[Tuple[str, LLMResponse]]) -> LLMResponse:
        """Combine responses using weighted voting"""
        if len(responses) == 1:
            return responses[0][1]
        
        # Score each response
        scored_responses = []
        for provider_name, response in responses:
            score = self._score_response(response)
            weight = self._get_provider_weight(provider_name)
            final_score = score * weight
            scored_responses.append((final_score, response))
        
        # Return highest scored response
        best_response = max(scored_responses, key=lambda x: x[0])[1]
        
        # Add ensemble metadata
        best_response.metadata = best_response.metadata or {}
        best_response.metadata.update({
            'ensemble_method': 'weighted',
            'ensemble_size': len(responses)
        })
        
        return best_response
    
    def _score_response(self, response: LLMResponse) -> float:
        """Score response quality"""
        score = 0.5  # Base score
        
        # Length factor
        if len(response.content) > 50:
            score += 0.2
        if len(response.content) > 200:
            score += 0.1
        
        # Avoid overly hedged responses
        hedge_words = ['might', 'could', 'possibly', 'perhaps', 'maybe']
        hedge_count = sum(1 for word in hedge_words if word in response.content.lower())
        score -= min(hedge_count * 0.05, 0.2)
        
        return max(0.0, min(1.0, score))
    
    def _get_provider_weight(self, provider_name: str) -> float:
        """Get weight for provider in ensemble voting"""
        if provider_name in self.provider_performance:
            perf = self.provider_performance[provider_name]
            return perf['success_rate']
        return 0.5
    
    def _update_provider_metrics(self, provider: BaseLLMProvider, bias_risk: float):
        """Update provider performance metrics"""
        provider_name = None
        for name, p in self.providers.items():
            if p == provider:
                provider_name = name
                break
        
        if provider_name and provider_name in self.provider_performance:
            metrics = self.provider_performance[provider_name]
            metrics['total_requests'] += 1
            
            # Track bias incidents
            if bias_risk > 0.7:
                metrics['bias_incidents'] += 1
    
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
        for provider_name in ['ollama_default', 'claude_default', 'gemini_default', 'openai_default']:
            if provider_name in self.providers:
                return provider_name
        
        return None
    
    def estimate_cost(self, text: str, provider_name: Optional[str] = None) -> float:
        """Estimate cost for processing text with given provider"""
        estimated_tokens = len(text.split()) * 1.3
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            
            cost_rates = {
                LLMProvider.OPENAI: 0.002,
                LLMProvider.ANTHROPIC: 0.009,
                LLMProvider.GOOGLE: 0.0007,
                LLMProvider.OLLAMA: 0.0,
            }
            
            rate = cost_rates.get(provider.config.provider, 0.001)
            return (estimated_tokens / 1000) * rate
        
        return 0.0