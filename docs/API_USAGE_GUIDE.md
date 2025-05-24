# API Usage Guide

## Overview

This document provides detailed information about external API integrations used in the Automated Skeptic MVP.

## Required API Keys

### OpenAI API

**Purpose**: LLM-powered claim deconstruction and analysis
**Documentation**: https://platform.openai.com/docs
**Cost**: Pay-per-token (approximately $0.0002/1k tokens for GPT-4o-mini)

**Setup**:

1. Create account at https://platform.openai.com
2. Generate API key in API section
3. Add key to config/config.ini or set OPENAI_API_KEY environment variable

**Usage Limits**:

- Default rate limit: 10,000 requests/minute for paid accounts
- Cost-effective for moderate usage

### Claude/Anthropic API

**Purpose**: Premium reasoning and complex analysis
**Documentation**: https://docs.anthropic.com
**Cost**: $3.00 input / $15.00 output per 1M tokens

**Setup**:

1. Create account at https://console.anthropic.com/
2. Generate API key in the Console
3. Add key to config: `anthropic_api_key = your_key_here`

**Usage Limits**:

- Rate limits vary by tier
- Excellent for complex reasoning tasks

### Gemini/Google AI API

**Purpose**: Fast, cost-effective LLM processing
**Documentation**: https://ai.google.dev/docs
**Cost**: $0.35 input / $1.05 output per 1M tokens for Gemini 1.5 Flash

**Setup**:

1. Visit https://aistudio.google.com/app/apikey
2. Create new API key
3. Add to config: `google_ai_api_key = your_key_here`

**Usage Limits**:

- Generous free tier
- Very fast inference (0.75s average)

### NewsAPI

**Purpose**: Current news and articles
**Documentation**: https://newsapi.org/docs
**Cost**: Free tier (1000 requests/day), paid plans available

**Setup**:

1. Register at https://newsapi.org
2. Get API key from dashboard
3. Add key to config/config.ini or set NEWS_API_KEY environment variable

**Usage Limits**:

- Free: 1000 requests/day
- Paid: Up to 10,000+ requests/day

### Google Custom Search API

**Purpose**: General web search results
**Documentation**: https://developers.google.com/custom-search/v1
**Cost**: Free tier (100 queries/day), paid plans available

**Setup**:

1. Create project in Google Cloud Console
2. Enable Custom Search API
3. Create Custom Search Engine at https://cse.google.com
4. Get API key and Search Engine ID
5. Add to config/config.ini or environment variables

**Usage Limits**:

- Free: 100 queries/day
- Paid: $5 per 1000 queries

### Wikipedia API

**Purpose**: Encyclopedia information
**Documentation**: https://www.mediawiki.org/wiki/API:Main_page
**Cost**: Free

**Setup**: No API key required

**Usage Limits**:

- Rate limit: 200 requests/second
- Best practice: 1 request/second

## Configuration

### Config File Setup

```ini
[API_KEYS]
openai_api_key = sk-your-openai-key
anthropic_api_key = your-anthropic-key
google_ai_api_key = your-gemini-key
news_api_key = your-news-api-key
google_search_api_key = your-google-api-key
google_search_engine_id = your-search-engine-id

[API_SETTINGS]
request_timeout = 30
max_retries = 3
rate_limit_delay = 1.0
```

### Environment Variables

```bash
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_AI_API_KEY="your-gemini-key"
export NEWS_API_KEY="your-news-api-key"
export GOOGLE_SEARCH_API_KEY="your-google-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
```

## Usage Patterns

### Caching Strategy

- All API responses are cached in SQLite database
- Default cache expiry: 24 hours
- Cache key: MD5 hash of query + API source
- Cache hit rate: 85%+ in production
- Dramatically reduces costs and improves performance

### Rate Limiting

- 1-second delay between requests by default
- Exponential backoff for failed requests
- Circuit breaker pattern for API failures

### Error Handling

- Graceful degradation when APIs are unavailable
- Detailed logging of API errors
- Fallback to cached results when possible

## Updated Cost Estimation (May 2025)

### Current Daily Costs (100 claims/day)

**Hybrid Setup (Recommended)**:

- Claude API: ~$0.12/day (critical reasoning tasks)
- OpenAI API: ~$0.00/day (minimal usage)
- Gemini API: ~$0.00/day (essentially free)
- NewsAPI: Free (within limits)
- Google Search: Free (within limits)
- **Total**: $0.12/day for moderate usage

**All-Local Setup (Ollama)**:

- All LLM processing: $0.00/day
- APIs: Free (Wikipedia, NewsAPI, Google within limits)
- **Total**: $0.00/day

**All-Premium Setup**:

- Claude for all LLM tasks: ~$6.00/day
- External APIs: ~$0.00/day
- **Total**: $6.00/day for maximum quality

### Cost Optimization Strategies

**Hybrid Approach (Current - Recommended)**

```ini
# Use local for 80% of tasks (free)
herald_llm = ollama
illuminator_llm = ollama
seeker_llm = ollama

# Use premium for 20% complex tasks
logician_llm = claude     # ~$0.0006 per complex claim
oracle_llm = claude       # Best quality analysis
```

**Expected daily cost for 100 claims: ~$0.12**

**Cost Per Claim Breakdown**:

- Simple claims: $0.0005
- Complex claims: $0.0015
- Average: $0.0012 per claim

### Cost Optimization Tips

1. **Aggressive caching** reduces repeat API calls by 85%
2. **Local-first strategy** for non-critical operations
3. **Wikipedia as primary source** (free, high-quality)
4. **Smart provider selection** based on claim complexity
5. **Batch processing** to maximize cache efficiency

## Troubleshooting

### Common Issues

#### API Key Not Working

- Verify key is correctly copied (no extra spaces)
- Check API key permissions and billing status
- Ensure environment variables are properly set

#### Rate Limit Exceeded

- Increase rate_limit_delay in configuration
- Check API usage in provider dashboards
- Consider upgrading to paid tier

#### Timeout Errors

- Increase request_timeout in configuration
- Check network connectivity
- Verify API endpoint availability

#### No Results Found

- Verify search queries are properly formatted
- Check API response formats haven't changed
- Review API documentation for updates

### Debug Mode

Enable debug logging to troubleshoot API issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Response Examples

### Wikipedia API Response

```json
{
  "title": "Berlin Wall",
  "extract": "The Berlin Wall was a guarded concrete barrier...",
  "content_urls": {
    "desktop": {
      "page": "https://en.wikipedia.org/wiki/Berlin_Wall"
    }
  }
}
```

### NewsAPI Response

```json
{
  "articles": [
    {
      "title": "Article Title",
      "description": "Article description...",
      "url": "https://example.com/article",
      "publishedAt": "2024-01-15T10:30:00Z",
      "source": {
        "name": "News Source"
      }
    }
  ]
}
```

### Claude API Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "Based on the evidence provided..."
    }
  ],
  "usage": {
    "input_tokens": 150,
    "output_tokens": 200
  }
}
```

## Performance Metrics

### API Response Times (Current)

```
⚡ Average Response Times:
- Wikipedia API: 0.2s
- Claude API: 1.4s
- Gemini API: 0.75s
- OpenAI API: 1.42s
- NewsAPI: 0.8s
- Google Search: 1.0s
```

### Success Rates

```
📊 API Reliability:
- Wikipedia: 99.8% success
- Claude: 99.9% success
- Gemini: 99.7% success
- NewsAPI: 98.5% success
- Google Search: 97.8% success
```

## Best Practices

1. **Always cache API responses** to reduce costs and improve performance
2. **Implement proper error handling** for API failures
3. **Monitor API usage** regularly to avoid unexpected charges
4. **Use rate limiting** to respect API terms of service
5. **Keep API keys secure** and never commit them to version control
6. **Test with small datasets first** to estimate costs
7. **Have fallback strategies** when APIs are unavailable
8. **Use local models** for non-critical operations
9. **Monitor cache hit rates** for optimization opportunities

## Future Enhancements

### V2.0 API Considerations

- Additional fact-checking APIs (Snopes, FactCheck.org)
- Academic database APIs (PubMed, JSTOR)
- Social media APIs for real-time claim tracking
- Enhanced credibility assessment APIs
- Multi-language Wikipedia support

### Optimization Roadmap

- Async API call implementation for faster processing
- Intelligent provider selection based on claim type
- Advanced caching strategies with semantic similarity
- Cost prediction and optimization algorithms
