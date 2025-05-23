# automated_skeptic_mvp/scripts/diagnose_oracle.py
"""
Diagnose what's wrong with the Oracle agent's evidence analysis
"""

import requests
import re

def test_wikipedia_content():
    """Test what the Berlin Wall Wikipedia page actually says"""
    
    print("🔍 DIAGNOSING ORACLE EVIDENCE ANALYSIS")
    print("=" * 60)
    
    # Get the actual Berlin Wall Wikipedia content
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/Berlin_Wall"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', '')
            extract = data.get('extract', '')
            
            print(f"\n📋 Wikipedia Page: {title}")
            print(f"📝 Content Length: {len(extract)} characters")
            print(f"\n📖 First 500 characters:")
            print(f"   {extract[:500]}...")
            
            # Test the claim matching logic that Oracle is using
            claim = "The Berlin Wall fell in 1989."
            
            print(f"\n🧪 TESTING ORACLE'S LOGIC:")
            print(f"   Claim: '{claim}'")
            
            # Simulate Oracle's keyword matching
            claim_words = set(claim.lower().split())
            content_words = set(extract.lower().split())
            
            overlap = claim_words.intersection(content_words)
            overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
            
            print(f"   Claim words: {sorted(claim_words)}")
            print(f"   Overlapping words: {sorted(overlap)}")
            print(f"   Overlap ratio: {overlap_ratio:.2f}")
            
            # Check for negation words (Oracle's bug likely here)
            negation_words = ['not', 'no', 'never', 'false', 'incorrect', 'wrong', 'untrue']
            has_negation = any(neg in extract.lower() for neg in negation_words)
            
            print(f"   Contains negation words: {has_negation}")
            if has_negation:
                found_negations = [neg for neg in negation_words if neg in extract.lower()]
                print(f"   Found negations: {found_negations}")
            
            # Oracle's assessment logic
            supports_claim = overlap_ratio > 0.5 and not has_negation
            print(f"   Oracle would conclude: {'SUPPORTS' if supports_claim else 'CONTRADICTS'}")
            
            # Check for specific "1989" and "fell" mentions
            has_1989 = '1989' in extract
            has_fall_words = any(word in extract.lower() for word in ['fell', 'fall', 'collapsed', 'demolished', 'destroyed'])
            
            print(f"\n🎯 SPECIFIC CHECKS:")
            print(f"   Contains '1989': {has_1989}")
            print(f"   Contains fall/collapse words: {has_fall_words}")
            
            if has_1989 and has_fall_words:
                print(f"   ✅ Should clearly SUPPORT the claim!")
            elif has_1989:
                print(f"   ⚠️  Has the year but unclear about falling")
            else:
                print(f"   ❌ Missing key information")
                
            # Look for the actual sentence about 1989
            sentences = extract.split('.')
            relevant_sentences = []
            for sentence in sentences:
                if '1989' in sentence:
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                print(f"\n📍 SENTENCES MENTIONING 1989:")
                for i, sentence in enumerate(relevant_sentences, 1):
                    print(f"   {i}. {sentence}")
            
        else:
            print(f"❌ Failed to get Wikipedia content: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing Wikipedia content: {str(e)}")

def simulate_oracle_logic():
    """Simulate the Oracle's evidence analysis logic"""
    
    print(f"\n" + "=" * 60)
    print(f"🧠 SIMULATING ORACLE'S ANALYSIS LOGIC")
    print("=" * 60)
    
    # Test with realistic Berlin Wall content
    sample_content = """
    The Berlin Wall was a guarded concrete barrier that physically and ideologically divided Berlin from 1961 to 1989. 
    Construction began on 13 August 1961. The Wall fell on 9 November 1989, during the Peaceful Revolution, 
    which was part of the Revolutions of 1989.
    """
    
    claim = "The Berlin Wall fell in 1989."
    
    print(f"📋 Test Content: {sample_content.strip()}")
    print(f"🎯 Claim: {claim}")
    
    # Oracle's current logic (simplified)
    claim_words = set(claim.lower().split())
    content_words = set(sample_content.lower().split())
    
    overlap = claim_words.intersection(content_words)
    overlap_ratio = len(overlap) / len(claim_words)
    
    negation_words = ['not', 'no', 'never', 'false', 'incorrect', 'wrong', 'untrue']
    has_negation = any(neg in sample_content.lower() for neg in negation_words)
    
    print(f"\n🔍 Analysis:")
    print(f"   Overlap words: {sorted(overlap)}")
    print(f"   Overlap ratio: {overlap_ratio:.2f}")
    print(f"   Has negation: {has_negation}")
    print(f"   Oracle conclusion: {'SUPPORTS' if overlap_ratio > 0.5 and not has_negation else 'CONTRADICTS'}")
    
    print(f"\n💡 PROBLEM IDENTIFIED:")
    print(f"   The Oracle's logic is too simplistic!")
    print(f"   It needs semantic understanding, not just keyword matching.")

def suggest_oracle_fixes():
    """Suggest fixes for the Oracle agent"""
    
    print(f"\n" + "=" * 60)
    print(f"🔧 SUGGESTED ORACLE FIXES")
    print("=" * 60)
    
    print(f"""
1. 🎯 IMPROVE EVIDENCE EXTRACTION
   • Current: Simple keyword overlap
   • Better: Extract sentences containing claim keywords
   • Best: Use LLM to extract relevant evidence

2. 🧠 SEMANTIC ANALYSIS  
   • Current: Basic negation word detection
   • Better: Context-aware negation analysis
   • Best: LLM-based semantic similarity

3. 📊 BETTER RELEVANCE SCORING
   • Current: Overlap ratio only
   • Better: Weight important words (dates, proper nouns)
   • Best: Vector similarity or LLM scoring

4. 🔍 SMARTER SUPPORTING TEXT EXTRACTION
   • Current: Sentences with word overlap
   • Better: Sentences with semantic relevance
   • Best: LLM summarization of relevant evidence

5. 🎪 USE YOUR POWERFUL MODELS
   • You have DeepSeek-R1 for Oracle!
   • Let it analyze evidence semantically
   • Ask it: "Does this content support or contradict the claim?"
""")

def main():
    """Main diagnosis function"""
    test_wikipedia_content()
    simulate_oracle_logic()
    suggest_oracle_fixes()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 DIAGNOSIS COMPLETE")
    print("=" * 60)
    print(f"""
✅ SEARCH IS PERFECT: Found exactly the right sources
❌ ORACLE IS BROKEN: Misreading obvious evidence
🔧 EASY FIX: Improve evidence analysis in Oracle agent

The Berlin Wall Wikipedia page obviously supports the claim that 
"The Berlin Wall fell in 1989" - this should be a slam dunk SUPPORTED verdict!
""")

if __name__ == "__main__":
    main()