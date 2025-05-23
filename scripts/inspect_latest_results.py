# automated_skeptic_mvp/scripts/inspect_latest_results.py
"""
Quick inspection of the latest results to see what sources were found
"""

import json
from pathlib import Path

def inspect_results():
    """Inspect the latest results.json"""
    
    results_file = "results.json"
    if not Path(results_file).exists():
        print(f"❌ Results file '{results_file}' not found")
        return
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print("🔍 LATEST RESULTS INSPECTION")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            claim = result.get('claim', 'Unknown')
            verdict = result.get('verdict', 'Unknown')
            confidence = result.get('confidence', 0)
            sources = result.get('sources', [])
            evidence_summary = result.get('evidence_summary', '')
            
            print(f"\n📋 Claim: {claim}")
            print(f"🎯 Verdict: {verdict} (confidence: {confidence:.1%})")
            print(f"📊 Found {len(sources)} sources")
            
            print(f"\n🔗 SOURCES ANALYSIS:")
            for j, source in enumerate(sources, 1):
                title = source.get('title', 'No Title')
                url = source.get('url', 'No URL')
                credibility = source.get('credibility', 0)
                
                print(f"   {j}. {title}")
                print(f"      URL: {url}")
                print(f"      Credibility: {credibility:.1f}")
                
                # Quick relevance check
                claim_words = set(claim.lower().split())
                title_words = set(title.lower().split())
                overlap = claim_words.intersection(title_words)
                
                if 'berlin' in title.lower() and 'wall' in title.lower():
                    print(f"      ✅ HIGHLY RELEVANT: Contains 'Berlin Wall'")
                elif len(overlap) >= 2:
                    print(f"      ✅ RELEVANT: Good word overlap ({overlap})")
                elif len(overlap) >= 1:
                    print(f"      ⚠️  PARTIAL: Some overlap ({overlap})")
                else:
                    print(f"      ❌ POOR: No obvious relevance")
            
            print(f"\n📝 Evidence Summary:")
            print(f"   {evidence_summary}")
            
            # Diagnosis
            print(f"\n🔬 DIAGNOSIS:")
            if len(sources) == 0:
                print(f"   ❌ No sources found - search not working")
            elif any('berlin' in s.get('title', '').lower() and 'wall' in s.get('title', '').lower() for s in sources):
                print(f"   ✅ Found Berlin Wall sources - issue likely in evidence analysis")
                print(f"   🔍 Check: How is the evidence being extracted and analyzed?")
            elif any('berlin' in s.get('title', '').lower() for s in sources):
                print(f"   ⚠️  Found Berlin-related sources - partial success")
            else:
                print(f"   ❌ No relevant sources - search terms need refinement")
            
            if verdict == 'CONTRADICTED' and confidence > 0.9:
                print(f"   🚨 HIGH CONFIDENCE CONTRADICTION - Check evidence analysis logic")
                print(f"   💡 The sources might be correct but evidence extraction is wrong")
    
    except Exception as e:
        print(f"❌ Error inspecting results: {str(e)}")

if __name__ == "__main__":
    inspect_results()