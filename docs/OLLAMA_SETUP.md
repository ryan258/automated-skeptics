# Ollama Integration Setup Guide

## Overview

This guide walks you through setting up Ollama for local LLM inference with the Automated Skeptic system. With Ollama, you can run powerful language models locally, providing privacy, cost savings, and independence from external APIs.

## Benefits of Local LLMs

### 🔒 **Privacy & Security**

- No data sent to external services
- Complete control over sensitive information
- Ideal for confidential fact-checking tasks

### 💰 **Cost Savings**

- No per-token charges
- No API rate limits
- Ideal for development and testing

### ⚡ **Performance**

- No network latency
- Consistent availability
- Customizable model selection

### 🔧 **Flexibility**

- Mix local and external models per agent
- Experiment with different models
- Easy model switching

## Installation

### Step 1: Install Ollama

#### On macOS

```bash
# Download and install from the official website
curl -fsSL https://ollama.ai/install.sh | sh

# Or using Homebrew
brew install ollama
```

#### On Linux

```bash
# Download and install
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama  # To start on boot
```

#### On Windows

1. Download Ollama from https://ollama.ai/download
2. Run the installer
3. Ollama will start automatically

### Step 2: Verify Installation

```bash
# Check if Ollama is running
ollama --version

# Should show version information
```

### Step 3: Pull Recommended Models

```bash
# Pull Llama 2 (7B parameters - good balance of performance and resource usage)
ollama pull llama2

# For better performance (if you have sufficient RAM):
ollama pull llama2:13b

# For lighter resource usage:
ollama pull llama2:7b-chat

# Alternative models to try:
ollama pull codellama  # Good for technical content
ollama pull mistral    # Fast and efficient
ollama pull neural-chat  # Optimized for conversations
```

### Step 4: Test Ollama

```bash
# Test basic functionality
ollama run llama2
# Type a test message and verify response

# List available models
ollama list

# Check running models
ollama ps
```

## Configuration

### Update Configuration File

Edit your `config/config.ini` file:

```ini
[LLM_MODELS]
# Enable Ollama
ollama_enabled = true

# Set default model (use one you've pulled)
ollama_model = llama2

# Ollama server URL (default for local installation)
ollama_base_url = http://localhost:11434

# Model parameters
ollama_temperature = 0.1
ollama_max_tokens = 500

[AGENT_LLM_MAPPING]
# Example: Use local LLM for lightweight tasks, OpenAI for complex reasoning

# Lightweight processing - use local
herald_llm = ollama
herald_model = llama2

illuminator_llm = ollama
illuminator_model = llama2

seeker_llm = ollama
seeker_model = llama2

# Complex reasoning - use OpenAI (if available) or fallback to local
logician_llm = openai
oracle_llm = openai

[COST_SETTINGS]
# Prefer local models to save costs
prefer_local = true
development_mode = true
```

## Model Recommendations

### By Task Type

| Agent           | Recommended Model      | Reasoning                            |
| --------------- | ---------------------- | ------------------------------------ |
| **Herald**      | `llama2` or `mistral`  | Simple text processing               |
| **Illuminator** | `llama2`               | Entity extraction and classification |
| **Logician**    | `llama2:13b` or OpenAI | Complex claim deconstruction         |
| **Seeker**      | `llama2`               | Research query generation            |
| **Oracle**      | `llama2:13b` or OpenAI | Evidence synthesis                   |

### By System Resources

| RAM Available | Recommended Model | Notes                  |
| ------------- | ----------------- | ---------------------- |
| **8GB**       | `llama2:7b-chat`  | Basic functionality    |
| **16GB**      | `llama2` (7B)     | Good performance       |
| **32GB+**     | `llama2:13b`      | Best local performance |

## Testing the Integration

### 1. Test LLM Manager

```python
from llm.manager import LLMManager
from config.settings import Settings

# Initialize
settings = Settings()
llm_manager = LLMManager(settings)

# Check available providers
print(llm_manager.get_available_providers())

# Test generation
response = llm_manager.generate(
    "Test message",
    agent_name="logician"
)
print(f"Response: {response.content}")
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
```

### 2. Test Agent Integration

```python
from agents.logician_agent import LogicianAgent
from data.models import Claim

# Initialize agent
settings = Settings()
logician = LogicianAgent(settings)

# Test claim processing
claim = Claim(text="The Berlin Wall fell in 1989.")
result = logician.process(claim)

print(f"Sub-claims: {len(result.sub_claims)}")
for i, sub_claim in enumerate(result.sub_claims):
    print(f"{i+1}. {sub_claim.text}")
```

### 3. Run Full Pipeline Test

```bash
# Test with local LLMs
python main.py --claim "Apple was founded in 1976." --config config/config.ini

# Check logs for LLM usage
tail -f automated_skeptic.log
```

## Performance Optimization

### Model Loading Optimization

```bash
# Preload models to reduce first-run latency
ollama run llama2 "Hello" --verbose

# Keep models in memory
# Add to your startup script:
ollama run llama2 &
```

### System Resource Monitoring

```bash
# Monitor Ollama resource usage
# On Linux:
htop -p $(pgrep ollama)

# On macOS:
activity monitor # Look for Ollama process

# Check model memory usage
ollama ps
```

### Performance Tuning

```ini
# In config.ini
[PERFORMANCE]
# Increase timeout for local models
local_llm_timeout = 120

# Enable parallel processing
enable_parallel_processing = true

# Cache LLM responses
enable_llm_caching = true
llm_cache_expiry = 24
```

## Troubleshooting

### Common Issues

#### 1. Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

#### 2. Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull llama2
```

#### 3. Memory Issues

```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Use smaller model
ollama pull llama2:7b-chat
```

#### 4. Slow Performance

- Ensure you have sufficient RAM
- Close other applications
- Use SSD storage for better I/O
- Consider using smaller models

### Debug Mode

Enable debug logging in `config.ini`:

```ini
[LOGGING]
level = DEBUG
llm_debug = true
```

## Advanced Configuration

### Custom Model Parameters

```ini
[LLM_MODELS]
# Custom Ollama parameters
ollama_additional_params = {
    "num_ctx": 4096,
    "num_gpu": 0,
    "num_thread": 8,
    "repeat_penalty": 1.1
}
```

### Multiple Ollama Instances

```ini
# Run different models on different ports
[LLM_MODELS]
ollama_fast_base_url = http://localhost:11434
ollama_slow_base_url = http://localhost:11435

[AGENT_LLM_MAPPING]
herald_llm = ollama_fast
logician_llm = ollama_slow
```

## Model Comparison

### Performance Benchmarks (Approximate)

| Model            | Size  | RAM Required | Speed  | Quality   |
| ---------------- | ----- | ------------ | ------ | --------- |
| `llama2:7b-chat` | 3.8GB | 8GB          | Fast   | Good      |
| `llama2` (7B)    | 3.8GB | 8GB          | Fast   | Good      |
| `llama2:13b`     | 7.3GB | 16GB         | Medium | Better    |
| `mistral`        | 4.1GB | 8GB          | Fast   | Good      |
| `codellama`      | 3.8GB | 8GB          | Fast   | Technical |

### Cost Comparison

| Scenario                 | OpenAI Cost/Day | Ollama Cost/Day | Savings |
| ------------------------ | --------------- | --------------- | ------- |
| Development (100 claims) | $2-5            | $0              | 100%    |
| Production (1000 claims) | $20-50          | $0              | 100%    |
| Heavy Usage (10k claims) | $200-500        | $0              | 100%    |

## Next Steps

1. **Install and test** Ollama with basic models
2. **Configure** agents to use appropriate LLM providers
3. **Benchmark** performance with your specific claims
4. **Optimize** model selection based on accuracy vs. speed needs
5. **Scale up** to larger models as needed

## Getting Help

### Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Model Library](https://ollama.ai/library)
- [Ollama GitHub](https://github.com/jmorganca/ollama)

### Community

- [Ollama Discord](https://discord.gg/ollama)
- [Reddit r/ollama](https://reddit.com/r/ollama)

The integration provides a powerful foundation for cost-effective, private, and flexible LLM usage in your fact-checking pipeline! 🚀
