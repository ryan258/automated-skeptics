#!/usr/bin/env python3
# Debug script to test Oracle evidence analysis directly

import sys
sys.path.append('.')

from agents.oracle_agent import OracleAgent
from config.settings import Settings
from data.models import Claim, Source, Evidence

def test_oracle_directly():
    """Test Oracle with mock Berlin Wall evidence"""
    print("🔍 TESTING ORACLE EVIDENCE ANALYSIS")
    print("=" * 50)
    
    settings = Settings()
    oracle = OracleAgent(settings)
    
    # Create a test claim
    claim = Claim(text="The Berlin Wall fell in 1989.")
    
    # Create mock sources that should clearly support the claim
    mock_sources = [
        Source(
            url="https://en.wikipedia.org/wiki/Berlin_Wall",
            title="Berlin Wall - Wikipedia",
            content="The Berlin Wall was a guarded concrete barrier that physically and ideologically divided Berlin from 1961 to 1989. The Wall fell on 9 November 1989, during the Peaceful Revolution.",
            source_type="wikipedia",
            credibility_score=0.9,
            relevance_score=0.95
        ),
        Source(
            url="https://example.com/berlin-wall-history",
            title="Fall of Berlin Wall 1989",
            content="On November 9, 1989, the Berlin Wall came down after 28 years of division. East German authorities announced new regulations allowing free passage between East and West Berlin.",
            source_type="news",
            credibility_score=0.8,
            relevance_score=0.9
        )
    ]
    
    # Add sources to claim
    claim.sources = mock_sources
    
    print(f"📋 Testing claim: {claim.text}")
    print(f"📊 Mock sources: {len(mock_sources)}")
    
    for i, source in enumerate(mock_sources, 1):
        print(f"   {i}. {source.title}")
        print(f"      Content: {source.content[:100]}...")
        print(f"      Credibility: {source.credibility_score}")
    
    print(f"\n🧪 Running Oracle analysis...")
    
    try:
        result = oracle.process(claim)
        
        print(f"\n📊 ORACLE RESULT:")
        print(f"   Verdict: {result.verdict}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Evidence Summary: {result.evidence_summary}")
        print(f"   Processing Time: {result.processing_time:.2f}s")
        
        if result.verdict == "SUPPORTED" and result.confidence > 0.7:
            print(f"\n✅ SUCCESS: Oracle correctly analyzed evidence")
        else:
            print(f"\n❌ PROBLEM: Oracle failed to recognize clear supporting evidence")
            print(f"\n🔧 Diagnosis:")
            print(f"   • Sources clearly mention Berlin Wall falling in 1989")
            print(f"   • Content has exact date: November 9, 1989")
            print(f"   • High credibility sources (Wikipedia)")
            print(f"   • Oracle should easily find this as SUPPORTED")
            
    except Exception as e:
        print(f"❌ Oracle failed: {str(e)}")

def test_oracle_basic_logic():
    """Test Oracle's basic evidence assessment logic"""
    print(f"\n" + "=" * 50)
    print(f"🧠 TESTING ORACLE'S BASIC LOGIC")
    print("=" * 50)
    
    # Test the basic assessment methods directly
    settings = Settings()
    oracle = OracleAgent(settings)
    
    claim_text = "The Berlin Wall fell in 1989."
    source_content = "The Berlin Wall fell on November 9, 1989, during the Peaceful Revolution."
    
    print(f"Claim: {claim_text}")
    print(f"Content: {source_content}")
    
    # Test basic support assessment
    if hasattr(oracle, '_assess_support_basic'):
        supports = oracle._assess_support_basic(claim_text, source_content)
        print(f"Basic Support Assessment: {supports}")
    
    # Test confidence calculation
    if hasattr(oracle, '_calculate_evidence_confidence_basic'):
        confidence = oracle._calculate_evidence_confidence_basic(claim_text, source_content, 0.9)
        print(f"Basic Confidence: {confidence:.2f}")
    
    # Test text extraction
    if hasattr(oracle, '_extract_supporting_text_basic'):
        supporting_text = oracle._extract_supporting_text_basic(claim_text, source_content)
        print(f"Supporting Text: {supporting_text}")

if __name__ == "__main__":
    test_oracle_directly()
    test_oracle_basic_logic()