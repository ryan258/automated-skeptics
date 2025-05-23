#!/usr/bin/env python3
# Debug why Seeker found 0 sources

import sys
sys.path.append('.')
import requests

def test_wikipedia_direct():
    """Test Wikipedia API directly"""
    print("🔍 Testing Wikipedia API directly...")
    
    # Test the exact Berlin Wall search
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/Berlin_Wall"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Title: {data.get('title', 'No title')}")
            print(f"Extract: {data.get('extract', 'No extract')[:200]}...")
            return True
        else:
            print(f"Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_seeker_search_terms():
    """Test Seeker search term extraction"""
    print("\n🔧 Testing Seeker search terms...")
    
    try:
        from agents.seeker_agent import SeekerAgent
        from config.settings import Settings
        
        settings = Settings()
        seeker = SeekerAgent(settings)
        
        query = "The Berlin Wall was physically dismantled beginning on November 9, 1989"
        terms = seeker._extract_search_terms(query)
        
        print(f"Query: {query}")
        print(f"Terms: {terms}")
        return len(terms) > 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚨 SEEKER DIAGNOSTIC")
    print("=" * 30)
    
    wiki_ok = test_wikipedia_direct()
    terms_ok = test_seeker_search_terms()
    
    if wiki_ok and terms_ok:
        print("\n✅ Both work - check Seeker error handling")
    elif not wiki_ok:
        print("\n❌ Wikipedia API issue")
    elif not terms_ok:
        print("\n❌ Search terms issue")