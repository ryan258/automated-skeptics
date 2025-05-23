# automated_skeptic_mvp/agents/seeker_agent.py
"""
Research Agent (The Seeker) - Streamlined research capabilities
Handles Wikipedia, news APIs, and fact-checking sites
"""

import logging
import time
import requests
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

from data.models import Claim, SubClaim, Source, Entity
from config.settings import Settings

class SeekerAgent:
    """Research and source gathering agent"""
    
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.cache_db = self._init_cache_db()
        
        # API configurations
        self.request_timeout = settings.getint('API_SETTINGS', 'request_timeout', 30)
        self.max_retries = settings.getint('API_SETTINGS', 'max_retries', 3)
        self.rate_limit_delay = settings.getfloat('API_SETTINGS', 'rate_limit_delay', 1.0)
        self.max_sources = settings.getint('PROCESSING', 'max_sources_per_claim', 5)
        
        # API keys
        self.news_api_key = settings.get('API_KEYS', 'news_api_key')
        self.google_api_key = settings.get('API_KEYS', 'google_search_api_key')
        self.google_engine_id = settings.get('API_KEYS', 'google_search_engine_id')
    
    def _init_cache_db(self) -> sqlite3.Connection:
        """Initialize SQLite cache database"""
        conn = sqlite3.connect('data/api_cache.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                query_hash TEXT PRIMARY KEY,
                api_source TEXT,
                response_data TEXT,
                timestamp DATETIME,
                expiry_time DATETIME
            )
        ''')
        
        conn.commit()
        return conn
    
    def process(self, claim: Claim) -> Claim:
        """
        Research claim and gather supporting sources
        
        Args:
            claim: Claim object with sub-claims to research
            
        Returns:
            Claim with sources populated
        """
        try:
            all_sources = []
            
            # Research each sub-claim
            for sub_claim in claim.sub_claims:
                if sub_claim.verifiable:
                    sources = self._research_sub_claim(sub_claim)
                    all_sources.extend(sources)
            
            # Remove duplicates and limit to max sources
            unique_sources = self._deduplicate_sources(all_sources)
            limited_sources = unique_sources[:self.max_sources]
            
            # Store sources in claim (we'll add this to the Claim model)
            if not hasattr(claim, 'sources'):
                claim.sources = []
            claim.sources = limited_sources
            
            self.logger.info(f"Seeker found {len(limited_sources)} sources")
            return claim
            
        except Exception as e:
            self.logger.error(f"Seeker processing error: {str(e)}")
            if not hasattr(claim, 'sources'):
                claim.sources = []
            return claim
    
    def _research_sub_claim(self, sub_claim: SubClaim) -> List[Source]:
        """Research a specific sub-claim"""
        sources = []
        
        # Sequential API integration as per roadmap
        
        # 1. Wikipedia API
        wikipedia_sources = self._search_wikipedia(sub_claim.text)
        sources.extend(wikipedia_sources)
        
        # 2. NewsAPI (if available)
        if self.news_api_key:
            news_sources = self._search_news(sub_claim.text)
            sources.extend(news_sources)
        
        # 3. Google Search API (if available)
        if self.google_api_key and self.google_engine_id:
            google_sources = self._search_google(sub_claim.text)
            sources.extend(google_sources)
        
        # Rate limiting
        time.sleep(self.rate_limit_delay)
        
        return sources
    
    def _search_wikipedia(self, query: str) -> List[Source]:
        """Search Wikipedia API"""
        sources = []
        
        try:
            # Check cache first
            cached_result = self._get_cached_result(query, 'wikipedia')
            if cached_result:
                return self._parse_wikipedia_response(cached_result)
            
            # Wikipedia search API
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            
            # Try to extract key terms for Wikipedia search
            search_terms = self._extract_search_terms(query)
            
            for term in search_terms[:3]:  # Limit to top 3 terms
                try:
                    url = search_url + term.replace(' ', '_')
                    response = requests.get(url, timeout=self.request_timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        source = Source(
                            url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            title=data.get('title', ''),
                            content=data.get('extract', ''),
                            source_type='wikipedia',
                            credibility_score=0.9,  # Wikipedia generally high credibility
                            relevance_score=self._calculate_relevance(query, data.get('extract', ''))
                        )
                        
                        sources.append(source)
                        
                        # Cache the result
                        self._cache_result(query, 'wikipedia', response.text)
                        
                except requests.RequestException as e:
                    self.logger.warning(f"Wikipedia API error for term '{term}': {str(e)}")
                    continue
                
        except Exception as e:
            self.logger.error(f"Wikipedia search error: {str(e)}")
        
        return sources
    
    def _search_news(self, query: str) -> List[Source]:
        """Search NewsAPI"""
        sources = []
        
        if not self.news_api_key:
            return sources
        
        try:
            # Check cache first
            cached_result = self._get_cached_result(query, 'newsapi')
            if cached_result:
                return self._parse_news_response(cached_result)
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'sortBy': 'relevancy',
                'pageSize': 5,
                'language': 'en'
            }
            
            response = requests.get(url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', []):
                    source = Source(
                        url=article.get('url', ''),
                        title=article.get('title', ''),
                        content=article.get('description', '') + ' ' + article.get('content', ''),
                        source_type='news',
                        credibility_score=self._assess_news_credibility(article.get('source', {}).get('name', '')),
                        relevance_score=self._calculate_relevance(query, article.get('description', '')),
                        publication_date=self._parse_date(article.get('publishedAt'))
                    )
                    
                    sources.append(source)
                
                # Cache the result
                self._cache_result(query, 'newsapi', response.text)
                
        except Exception as e:
            self.logger.error(f"NewsAPI search error: {str(e)}")
        
        return sources
    
    def _search_google(self, query: str) -> List[Source]:
        """Search Google Custom Search API"""
        sources = []
        
        if not self.google_api_key or not self.google_engine_id:
            return sources
        
        try:
            # Check cache first
            cached_result = self._get_cached_result(query, 'google')
            if cached_result:
                return self._parse_google_response(cached_result)
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_engine_id,
                'q': query,
                'num': 5
            }
            
            response = requests.get(url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    source = Source(
                        url=item.get('link', ''),
                        title=item.get('title', ''),
                        content=item.get('snippet', ''),
                        source_type='web',
                        credibility_score=self._assess_domain_credibility(item.get('link', '')),
                        relevance_score=self._calculate_relevance(query, item.get('snippet', ''))
                    )
                    
                    sources.append(source)
                
                # Cache the result
                self._cache_result(query, 'google', response.text)
                
        except Exception as e:
            self.logger.error(f"Google Search error: {str(e)}")
        
        return sources
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract key search terms from query"""
        # Simple extraction - can be enhanced
        import re
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'was', 'were', 'is', 'are'}
        
        words = re.findall(r'\b\w+\b', query.lower())
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Also include full query
        terms = [query] + key_terms
        
        return terms
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        if not content:
            return 0.0
        
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
    
    def _assess_news_credibility(self, source_name: str) -> float:
        """Assess credibility of news source"""
        # Simple credibility scoring - can be enhanced with a proper database
        high_credibility = ['Reuters', 'Associated Press', 'BBC', 'NPR', 'PBS']
        medium_credibility = ['CNN', 'Fox News', 'MSNBC', 'Wall Street Journal', 'New York Times']
        
        source_lower = source_name.lower()
        
        for source in high_credibility:
            if source.lower() in source_lower:
                return 0.9
        
        for source in medium_credibility:
            if source.lower() in source_lower:
                return 0.7
        
        return 0.5  # Default credibility
    
    def _assess_domain_credibility(self, url: str) -> float:
        """Assess credibility based on domain"""
        if not url:
            return 0.5
        
        high_credibility_domains = ['wikipedia.org', 'britannica.com', 'gov', 'edu']
        medium_credibility_domains = ['bbc.com', 'reuters.com', 'ap.org']
        
        url_lower = url.lower()
        
        for domain in high_credibility_domains:
            if domain in url_lower:
                return 0.9
        
        for domain in medium_credibility_domains:
            if domain in url_lower:
                return 0.8
        
        return 0.5
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Handle ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _deduplicate_sources(self, sources: List[Source]) -> List[Source]:
        """Remove duplicate sources based on URL"""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url and source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Sort by relevance and credibility
        unique_sources.sort(key=lambda s: (s.relevance_score + s.credibility_score) / 2, reverse=True)
        
        return unique_sources
    
    def _get_cache_key(self, query: str, api_source: str) -> str:
        """Generate cache key for query"""
        return hashlib.md5(f"{query}_{api_source}".encode()).hexdigest()
    
    def _get_cached_result(self, query: str, api_source: str) -> Optional[str]:
        """Get cached API result if available and not expired"""
        try:
            cache_key = self._get_cache_key(query, api_source)
            cursor = self.cache_db.cursor()
            
            cursor.execute(
                "SELECT response_data FROM api_cache WHERE query_hash = ? AND api_source = ? AND expiry_time > ?",
                (cache_key, api_source, datetime.now())
            )
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Cache retrieval error: {str(e)}")
            return None
    
    def _cache_result(self, query: str, api_source: str, response_data: str):
        """Cache API result"""
        try:
            cache_key = self._get_cache_key(query, api_source)
            expiry_time = datetime.now() + timedelta(hours=24)  # 24-hour cache
            
            cursor = self.cache_db.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO api_cache (query_hash, api_source, response_data, timestamp, expiry_time) VALUES (?, ?, ?, ?, ?)",
                (cache_key, api_source, response_data, datetime.now(), expiry_time)
            )
            
            self.cache_db.commit()
            
        except Exception as e:
            self.logger.error(f"Cache storage error: {str(e)}")
    
    def _parse_wikipedia_response(self, response_data: str) -> List[Source]:
        """Parse cached Wikipedia response"""
        # This would parse the cached JSON response
        # Implementation depends on the specific response format
        return []
    
    def _parse_news_response(self, response_data: str) -> List[Source]:
        """Parse cached NewsAPI response"""
        # This would parse the cached JSON response
        return []
    
    def _parse_google_response(self, response_data: str) -> List[Source]:
        """Parse cached Google Search response"""
        # This would parse the cached JSON response
        return []
