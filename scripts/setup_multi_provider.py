#!/usr/bin/env python3
# automated_skeptic_mvp/scripts/setup_multi_provider.py
"""
Setup script for multi-provider LLM integration (OpenAI + Claude + Gemini + Ollama)
"""

import subprocess
import sys
import os
from pathlib import Path

def install_packages():
    """Install required packages for all LLM providers"""
    
    packages = [
        "openai>=1.0.0",           # OpenAI API
        "anthropic>=0.25.0",       # Claude/Anthropic API
        "google-generativeai>=0.3.0",  # Gemini/Google AI API
        "httpx>=0.24.0",           # For async requests (Ollama)
    ]
    
    print("📦 Installing LLM provider packages...")
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Warning: Failed to install {package}: {e.stderr}")
            print(f"       You can install manually: pip install {package}")

def create_provider_files():
    """Create the new provider files"""
    
    providers_dir = Path("llm/providers")
    providers_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Claude provider
    claude_provider_code = '''# automated_skeptic_mvp/llm/providers/claude_provider.py
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
'''
    
    # Create Gemini provider
    gemini_provider_code = '''# automated_skeptic_mvp/llm/providers/gemini_provider.py
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
        full_prompt = "\\n\\n".join(prompt_parts)
        
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
'''
    
    # Write provider files
    claude_file = providers_dir / "claude_provider.py"
    gemini_file = providers_dir / "gemini_provider.py"
    
    with open(claude_file, 'w', encoding='utf-8') as f:
        f.write(claude_provider_code)
    print(f"✅ Created Claude provider: {claude_file}")
    
    with open(gemini_file, 'w', encoding='utf-8') as f:
        f.write(gemini_provider_code)
    print(f"✅ Created Gemini provider: {gemini_file}")

def update_base_and_manager():
    """Update base.py and manager.py files"""
    
    # Backup existing files
    base_file = Path("llm/base.py")
    manager_file = Path("llm/manager.py")
    
    if base_file.exists():
        backup_file = base_file.with_suffix('.py.backup')
        if not backup_file.exists():
            import shutil
            shutil.copy2(base_file, backup_file)
            print(f"✅ Backed up {base_file} to {backup_file}")
    
    if manager_file.exists():
        backup_file = manager_file.with_suffix('.py.backup')
        if not backup_file.exists():
            import shutil
            shutil.copy2(manager_file, backup_file)
            print(f"✅ Backed up {manager_file} to {backup_file}")
    
    print("ℹ️  Base.py and manager.py need manual updates")
    print("   Please replace them with the updated versions provided")

def create_config_example():
    """Create example configuration with all providers"""
    
    config_file = Path("config/multi_provider_config.ini")
    config_file.parent.mkdir(exist_ok=True)
    
    config_content = '''# automated_skeptic_mvp/config/multi_provider_config.ini
# Configuration with ALL LLM providers: OpenAI, Claude, Gemini, Ollama

[API_KEYS]
# OpenAI API key
openai_api_key = your_openai_api_key_here

# Anthropic/Claude API key
anthropic_api_key = your_anthropic_api_key_here

# Google AI/Gemini API key
google_ai_api_key = your_google_ai_api_key_here

# News and search APIs (existing)
news_api_key = your_news_api_key_here
google_search_api_key = your_google_search_api_key_here
google_search_engine_id = your_search_engine_id_here

[API_SETTINGS]
request_timeout = 30
max_retries = 3
rate_limit_delay = 1.0

[PROCESSING]
max_sources_per_claim = 5
confidence_threshold = 0.7
cache_expiry_hours = 24

[LLM_MODELS]
# === OPENAI CONFIGURATION ===
openai_model = gpt-4o-mini
openai_temperature = 0.1
openai_max_tokens = 500

# === CLAUDE/ANTHROPIC CONFIGURATION ===
claude_model = claude-3-5-sonnet-20241022
claude_temperature = 0.1
claude_max_tokens = 500

# === GEMINI/GOOGLE AI CONFIGURATION ===
gemini_model = gemini-1.5-flash
gemini_temperature = 0.1
gemini_max_tokens = 500

# === OLLAMA CONFIGURATION ===
ollama_enabled = true
ollama_model = llama2:latest
ollama_base_url = http://localhost:11434
ollama_temperature = 0.1
ollama_max_tokens = 500

[AGENT_LLM_MAPPING]
# LOCAL-FIRST STRATEGY (Cost Effective)
herald_llm = ollama
herald_model = phi3:latest
herald_temperature = 0.0
herald_max_tokens = 200

illuminator_llm = ollama
illuminator_model = llama3.2:latest
illuminator_temperature = 0.1
illuminator_max_tokens = 300

logician_llm = claude  # Complex reasoning
logician_model = claude-3-5-sonnet-20241022
logician_temperature = 0.1
logician_max_tokens = 600

seeker_llm = ollama
seeker_model = llama3.2:latest
seeker_temperature = 0.0
seeker_max_tokens = 200

oracle_llm = claude  # Critical analysis
oracle_model = claude-3-5-sonnet-20241022
oracle_temperature = 0.1
oracle_max_tokens = 800

[COST_SETTINGS]
prefer_local = true
max_daily_cost = 10.0
development_mode = true

[PERFORMANCE]
enable_parallel_processing = false
local_llm_timeout = 60
external_llm_timeout = 30
enable_llm_caching = true
llm_cache_expiry = 24
'''
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Created multi-provider config: {config_file}")

def test_providers():
    """Test if the new providers work"""
    print("\\n🧪 Testing new providers...")
    
    try:
        # Test Anthropic
        try:
            import anthropic
            print("✅ Anthropic package available")
        except ImportError:
            print("❌ Anthropic package not available")
        
        # Test Google AI
        try:
            import google.generativeai
            print("✅ Google AI package available")
        except ImportError:
            print("❌ Google AI package not available")
            
    except Exception as e:
        print(f"⚠️  Error testing providers: {str(e)}")

def main():
    """Main setup function"""
    print("🚀 MULTI-PROVIDER LLM SETUP")
    print("Setting up Claude + Gemini + OpenAI + Ollama integration")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("llm").exists():
        print("❌ Not in the correct directory!")
        print("💡 Run this script from the automated_skeptic_mvp root directory")
        return
    
    try:
        # Step 1: Install packages
        install_packages()
        
        # Step 2: Create provider files
        print("\\n📁 Creating provider files...")
        create_provider_files()
        
        # Step 3: Update base and manager (manual step)
        print("\\n🔧 Backing up existing files...")
        update_base_and_manager()
        
        # Step 4: Create config example
        print("\\n⚙️  Creating configuration...")
        create_config_example()
        
        # Step 5: Test providers
        test_providers()
        
        print("\\n" + "=" * 60)
        print("✅ MULTI-PROVIDER SETUP COMPLETE!")
        print("\\n📋 Next Steps:")
        print("   1. Replace llm/base.py with updated version")
        print("   2. Replace llm/manager.py with updated version") 
        print("   3. Copy config/multi_provider_config.ini to config/config.ini")
        print("   4. Add your API keys to config.ini:")
        print("      • OpenAI: openai_api_key")
        print("      • Claude: anthropic_api_key") 
        print("      • Gemini: google_ai_api_key")
        print("   5. Test with: python main.py --claim 'Test claim'")
        
        print("\\n🎯 You'll have access to:")
        print("   • 🏠 Ollama (local, free)")
        print("   • 🧠 Claude (best reasoning)")
        print("   • ⚡ Gemini (fast, cost-effective)")
        print("   • 🔧 OpenAI (reliable fallback)")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        print("\\n🔧 Manual installation:")
        print("   pip install anthropic google-generativeai")

if __name__ == "__main__":
    main()