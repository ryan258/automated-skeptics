#!/usr/bin/env python3
# automated_skeptic_mvp/scripts/test_phase6_features.py
"""
Phase 6 Test Runner - Truth Coherency Testing
"""

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_truth_coherency():
    print("🔍 PHASE 6: TRUTH COHERENCY TESTING")
    print("=" * 50)
    
    try:
        from testing.coherency_tester import CoherencyTester
        from pipeline.orchestrator import SkepticPipeline
        from config.settings import Settings
        
        settings = Settings()
        pipeline = SkepticPipeline(settings)
        tester = CoherencyTester(pipeline)
        
        print("✅ Pipeline initialized")
        
        print("\n🧪 Running truth coherency test...")
        results = tester.run_minimal_truth_test()
        
        print(f"\n📊 RESULTS:")
        print(f"   Total: {results['total_cases']}")
        print(f"   Passed: {results['passed']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Score: {results['coherency_score']:.1%}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(results['detailed_results'], 1):
            status = "✅" if result['passed'] else "❌"
            bias_info = "🚨" if result['bias_detected']['bias_detected'] else "✓"
            
            print(f"   {i}. {status} {result['test_case'][:40]}...")
            print(f"      Expected: {result['expected_verdict']} | Got: {result['actual_verdict']}")
            print(f"      Confidence: {result['actual_confidence']:.2f} | Bias: {bias_info}")
        
        if results['coherency_score'] >= 0.8:
            print(f"\n🎉 EXCELLENT: Strong truth-finding capability!")
        elif results['coherency_score'] >= 0.6:
            print(f"\n👍 GOOD: Reasonable performance")
        else:
            print(f"\n⚠️  NEEDS WORK: Truth-finding needs improvement")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None

def test_berlin_wall_claim():
    print("\n\n🏛️  BERLIN WALL BIAS TEST")
    print("=" * 50)
    
    try:
        from pipeline.orchestrator import SkepticPipeline
        from config.settings import Settings
        from data.models import Claim
        
        settings = Settings()
        pipeline = SkepticPipeline(settings)
        
        claim = Claim(text="The Berlin Wall fell in 1989.")
        
        print("🧪 Testing: 'The Berlin Wall fell in 1989.'")
        
        result = pipeline.process_claim(claim)
        
        print(f"\n📊 RESULT:")
        print(f"   Verdict: {result.verdict}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Time: {result.processing_time:.2f}s")
        
        # Check for bias detection
        bias_detected = False
        if hasattr(result, 'metadata') and result.metadata:
            if result.metadata.get('bias_risk_score', 0) > 0.3:
                bias_detected = True
                print(f"   Bias Risk: {result.metadata['bias_risk_score']:.1%}")
        
        if result.verdict == "SUPPORTED" and result.confidence > 0.7:
            print(f"\n✅ SUCCESS: Correctly identified historical fact")
        elif result.verdict == "INSUFFICIENT_EVIDENCE" and bias_detected:
            print(f"\n⚠️  BIAS DETECTED: Provider avoided politically sensitive fact")
        else:
            print(f"\n❌ ISSUE: Unexpected result for clear historical fact")
        
        return result
        
    except Exception as e:
        print(f"❌ Berlin Wall test failed: {str(e)}")
        return None

def validate_system_setup():
    print("🔧 SYSTEM VALIDATION")
    print("=" * 30)
    
    issues = []
    
    try:
        from pipeline.orchestrator import SkepticPipeline
        print("✅ Pipeline: Available")
    except ImportError:
        print("❌ Pipeline: Missing")
        issues.append("Pipeline not found")
    
    try:
        from testing.coherency_tester import CoherencyTester
        print("✅ Coherency Tester: Available")
    except ImportError:
        print("❌ Coherency Tester: Missing")
        issues.append("Coherency Tester not found")
    
    try:
        from config.settings import Settings
        Settings()
        print("✅ Configuration: Loaded")
    except Exception as e:
        print(f"⚠️  Configuration: Using defaults")
    
    if issues:
        print(f"\n⚠️  Issues: {len(issues)}")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print(f"\n🎉 All components available!")
        return True

def main():
    setup_logging()
    
    print("🚀 AUTOMATED SKEPTIC - PHASE 6 TESTING")
    print("Focus: Truth Coherency")
    print("=" * 60)
    
    if not validate_system_setup():
        print("\n❌ System validation failed.")
        return
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: Truth coherency
    coherency_results = test_truth_coherency()
    if coherency_results and coherency_results['coherency_score'] >= 0.6:
        tests_passed += 1
    
    # Test 2: Berlin Wall bias case
    berlin_result = test_berlin_wall_claim()
    if berlin_result and (berlin_result.verdict == "SUPPORTED" or berlin_result.confidence > 0.5):
        tests_passed += 1
    
    print(f"\n" + "=" * 60)
    print(f"🏁 PHASE 6 TEST SUMMARY")
    print(f"   Tests Passed: {tests_passed}/{tests_total}")
    print(f"   Success Rate: {tests_passed/tests_total:.1%}")
    
    if tests_passed == tests_total:
        print(f"🎉 ALL TESTS PASSED - Phase 6 working correctly!")
    elif tests_passed >= 1:
        print(f"👍 MOSTLY WORKING - Minor issues to address")
    else:
        print(f"⚠️  NEEDS WORK - Issues found")

if __name__ == "__main__":
    main()