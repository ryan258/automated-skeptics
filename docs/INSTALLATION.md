## Multi-Provider LLM Setup

### Quick Start (All Providers)

```bash
# 1. Install all LLM provider packages
pip install openai>=1.0.0 anthropic>=0.25.0 google-generativeai>=0.3.0

# 2. Get API keys (optional - can use Ollama only)
# OpenAI: https://platform.openai.com/api-keys
# Claude: https://console.anthropic.com/
# Gemini: https://aistudio.google.com/app/apikey

# 3. Configure in config/config.ini
cp config/example.config.ini config/config.ini
# Edit config.ini with your API keys

# 4. Test multi-provider setup
python scripts/demo_all_providers.py
```
