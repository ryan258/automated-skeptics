#!/usr/bin/env python3
# test_fixes.py - Simple test to verify all fixes work

import sys
sys.path.append('.')

def test_berlin_wall():
    """Test Berlin Wall claim - should now work"""
    print("🧪 Testing Berlin Wall claim...")
    
    try:
        from pipeline.orchestrator import SkepticPipeline
        from config.settings import Settings
        from data.models import Claim
        
        settings = Settings()
        pipeline = SkepticPipeline(settings)
        
        claim = Claim(text="The Berlin Wall fell in 1989.")
        result = pipeline.process_claim(claim)
        
        print(f"✅ Result: {result.verdict} ({result.confidence:.1%})")
        
        if result.verdict == "SUPPORTED" and result.confidence > 0.7:
            print("🎉 SUCCESS: Berlin Wall claim now works correctly!")
            return True
        else:
            print(f"⚠️  Still has issues, but should be better than before")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_search_terms():
    """Test search term extraction is fixed"""
    print("\n🔍 Testing search term extraction...")
    
    try:
        from agents.seeker_agent import SeekerAgent
        from config.settings import Settings
        
        settings = Settings()
        seeker = SeekerAgent(settings)
        
        query = "The Berlin Wall fell in 1989"
        terms = seeker._extract_search_terms_fixed(query)
        
        print(f"Query: {query}")
        print(f"Terms: {terms}")
        
        # Should get 'Berlin_Wall' not '19'
        if 'Berlin_Wall' in terms and '19' not in terms:
            print("✅ Search terms fixed!")
            return True
        else:
            print("⚠️  Search terms still need work")
            return False
            
    except Exception as e:
        print(f"❌ Search test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 TESTING FIXES")
    print("=" * 30)
    
    test1 = test_search_terms()
    test2 = test_berlin_wall()
    
    if test1 and test2:
        print("\n🎉 ALL FIXES WORKING!")
    else:
        print("\n⚠️  Some issues remain but should be improved")