# Example LLM Optimization Configurations

# === SPEED-OPTIMIZED SETUP ===

[AGENT_LLM_MAPPING_SPEED]

# Use fastest models for quick processing

herald_llm = ollama
herald_model = llama3.2:latest # Smaller, faster model

illuminator_llm = ollama  
illuminator_model = llama3.2:latest # Good for entity extraction

logician_llm = ollama
logician_model = llama3.1:latest # Larger model for reasoning

seeker_llm = ollama
seeker_model = llama3.2:latest # Quick query generation

oracle_llm = ollama
oracle_model = llama3.1:latest # Best reasoning for final verdict

# === QUALITY-OPTIMIZED SETUP ===

[AGENT_LLM_MAPPING_QUALITY]

# Use best models regardless of speed

herald_llm = ollama
herald_model = llama3.2:latest # Still efficient for simple tasks

illuminator_llm = ollama
illuminator_model = llama3.1:latest # Better entity understanding

logician_llm = ollama
logician_model = deepseek-r1:14b # Your most powerful local model

seeker_llm = ollama  
seeker_model = llama3.1:latest # Better research planning

oracle_llm = ollama
oracle_model = deepseek-r1:14b # Best model for critical decisions

# === COST/QUALITY HYBRID ===

[AGENT_LLM_MAPPING_HYBRID]

# Mix local and external strategically

herald_llm = ollama
herald_model = llama3.2:latest # Local for simple tasks

illuminator_llm = ollama
illuminator_model = llama3.1:latest # Local for classification

logician_llm = openai # External for complex reasoning
logician_model = gpt-4 # Best for claim deconstruction

seeker_llm = ollama
seeker_model = llama3.1:latest # Local for research planning

oracle_llm = openai # External for final verdict
oracle_model = gpt-4 # Critical decision making

# === SPECIALIZED MODEL SETUP ===

[AGENT_LLM_MAPPING_SPECIALIZED]

# Use models optimized for specific tasks

herald_llm = ollama
herald_model = phi3:latest # Efficient for text processing

illuminator_llm = ollama
illuminator_model = mistral:latest # Good for classification

logician_llm = ollama  
logician_model = deepseek-r1:14b # Reasoning specialist

seeker_llm = ollama
seeker_model = llama3.1:latest # General purpose

oracle_llm = ollama
oracle_model = finalend/hermes-3-llama-3.1:latest # Advanced reasoning
