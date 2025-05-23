# Multi-Provider Performance Analysis

## Benchmark Results (May 23, 2025)

### Speed Performance

```
🏃 Speed Ranking:
1. gemini_default: 0.75s    (🥇 FASTEST)
2. claude_default: 1.40s    (🥈 PREMIUM FAST)
3. openai_default: 1.42s    (🥉 RELIABLE)
4. seeker_llm: 2.25s        (Local fast)
5. herald_llm: 5.49s        (Local medium)
6. illuminator_llm: 6.00s   (Local medium)
7. ollama_default: 6.49s    (Local comprehensive)
```

### Cost Analysis

```
💰 Cost per Request:
1. All Ollama models: $0.0000  (FREE)
2. OpenAI gpt-4o-mini: ~$0.0000 (Essentially free)
3. Gemini Flash: ~$0.0000 (Extremely cheap)
4. Claude Sonnet: $0.0006 (Premium but affordable)
```

### Quality Assessment

| Provider | Reasoning Quality | Response Accuracy | Consistency |
| -------- | ----------------- | ----------------- | ----------- |
| Claude   | ⭐⭐⭐⭐⭐        | ⭐⭐⭐⭐⭐        | ⭐⭐⭐⭐⭐  |
| OpenAI   | ⭐⭐⭐⭐          | ⭐⭐⭐⭐⭐        | ⭐⭐⭐⭐⭐  |
| Gemini   | ⭐⭐⭐⭐          | ⭐⭐⭐⭐          | ⭐⭐⭐⭐    |
| Ollama   | ⭐⭐⭐            | ⭐⭐⭐            | ⭐⭐⭐⭐    |

## Optimal Configuration Recommendations

### Production Setup (Recommended)

- **Input Processing**: Ollama (free, fast enough)
- **Complex Reasoning**: Claude (best quality)
- **Evidence Analysis**: Claude (critical accuracy)
- **Search Planning**: Ollama (free, adequate)

**Expected cost**: ~$0.12/day for 100 claims
**Quality**: Enterprise-grade reasoning and analysis
