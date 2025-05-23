# API Usage Guide

## Overview

This document provides detailed information about external API integrations used in the Automated Skeptic MVP.

## Required API Keys

### OpenAI API

**Purpose**: LLM-powered claim deconstruction
**Documentation**: https://platform.openai.com/docs
**Cost**: Pay-per-token (approximately $0.002/1k tokens for GPT-3.5-turbo)

**Setup**:

1. Create account at https://platform.openai.com
2. Generate API key in API section
3. Add key to config/config.ini or set OPENAI_API_KEY environment variable

**Usage Limits**:

- Default rate limit: 3 requests/minute for free tier
- Increase limits by adding payment method

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
export NEWS_API_KEY="your-news-api-key"
export GOOGLE_SEARCH_API_KEY="your-google-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
```

## Usage Patterns

### Caching Strategy

- All API responses are cached in SQLite database
- Default cache expiry: 24 hours
- Cache key: MD5 hash of query + API source
- Reduces costs and improves performance

### Rate Limiting

- 1-second delay between requests by default
- Exponential backoff for failed requests
- Circuit breaker pattern for API failures

### Error Handling

- Graceful degradation when APIs are unavailable
- Detailed logging of API errors
- Fallback to cached results when possible

## Cost Estimation

### Expected Daily Costs (100 claims/day)

- OpenAI API: ~$0.50-2.00/day
- NewsAPI: Free (within limits)
- Google Search: Free (within limits)
- **Total**: <$2.00/day for moderate usage

### Cost Optimization Tips

1. Aggressive caching reduces repeat API calls
2. Process claims in batches to maximize cache efficiency
3. Use Wikipedia API as primary source (free)
4. Monitor usage through API dashboards

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

## Best Practices

1. **Always cache API responses** to reduce costs and improve performance
2. **Implement proper error handling** for API failures
3. **Monitor API usage** regularly to avoid unexpected charges
4. **Use rate limiting** to respect API terms of service
5. **Keep API keys secure** and never commit them to version control
6. **Test with small datasets first** to estimate costs
7. **Have fallback strategies** when APIs are unavailable

## Future Enhancements

### V2.0 API Considerations

- Additional fact-checking APIs (Snopes, FactCheck.org)
- Academic database APIs (PubMed, JSTOR)
- Social media APIs for real-time claim tracking
- Enhanced credibility assessment APIs
