# automated_skeptic_mvp/testing/coherency_tester.py
"""
Truth Coherency Testing Framework
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class TruthTestCase:
    """Test case for truth verification"""
    claim: str
    expected_verdict: str
    expected_confidence_min: float
    category: str
    known_truth_value: bool
    bias_risk_level: str
    test_reasoning: str

class CoherencyTester:
    """Tests system's ability to find truth consistently"""
    
    def __init__(self, pipeline):
        self.logger = logging.getLogger(__name__)
        self.pipeline = pipeline
    
    def run_truth_coherency_test(self) -> Dict[str, Any]:
        """Run comprehensive truth coherency testing"""
        
        test_cases = self._load_truth_test_cases()
        results = {
            'total_cases': len(test_cases),
            'passed': 0,
            'failed': 0,
            'coherency_score': 0.0,
            'detailed_results': []
        }
        
        for test_case in test_cases:
            try:
                result = self._test_single_case(test_case)
                results['detailed_results'].append(result)
                
                if result['passed']:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                self.logger.error(f"Test case failed: {test_case.claim} - {str(e)}")
                results['failed'] += 1
        
        results['coherency_score'] = results['passed'] / results['total_cases'] if results['total_cases'] > 0 else 0
        
        return results
    
    def _test_single_case(self, test_case: TruthTestCase) -> Dict[str, Any]:
        """Test a single truth case"""
        
        from data.models import Claim
        claim = Claim(text=test_case.claim)
        
        # Process through pipeline
        verification_result = self.pipeline.process_claim(claim)
        
        # Evaluate result
        verdict_correct = verification_result.verdict == test_case.expected_verdict
        confidence_adequate = verification_result.confidence >= test_case.expected_confidence_min
        truth_aligned = self._check_truth_alignment(
            test_case.known_truth_value,
            verification_result.verdict,
            verification_result.confidence
        )
        
        passed = verdict_correct and confidence_adequate and truth_aligned
        
        result = {
            'test_case': test_case.claim,
            'category': test_case.category,
            'bias_risk': test_case.bias_risk_level,
            'expected_verdict': test_case.expected_verdict,
            'actual_verdict': verification_result.verdict,
            'expected_confidence_min': test_case.expected_confidence_min,
            'actual_confidence': verification_result.confidence,
            'known_truth': test_case.known_truth_value,
            'verdict_correct': verdict_correct,
            'confidence_adequate': confidence_adequate,
            'truth_aligned': truth_aligned,
            'passed': passed,
            'processing_time': verification_result.processing_time,
            'bias_detected': self._extract_bias_info(verification_result)
        }
        
        return result
    
    def _check_truth_alignment(self, known_truth: bool, verdict: str, confidence: float) -> bool:
        """Check if system result aligns with known truth"""
        
        if known_truth:
            # True facts should be SUPPORTED with good confidence
            return verdict == "SUPPORTED" and confidence > 0.6
        else:
            # False facts should be CONTRADICTED or at least not strongly supported
            return verdict in ["CONTRADICTED", "INSUFFICIENT_EVIDENCE"] or confidence < 0.5
    
    def _extract_bias_info(self, verification_result) -> Dict[str, Any]:
        """Extract bias-related information from result"""
        
        bias_info = {
            'bias_detected': False,
            'bias_score': 0.0,
            'provider_switched': False
        }
        
        if hasattr(verification_result, 'metadata') and verification_result.metadata:
            metadata = verification_result.metadata
            
            if 'bias_risk_score' in metadata:
                bias_info['bias_score'] = metadata['bias_risk_score']
                bias_info['bias_detected'] = bias_info['bias_score'] > 0.3
            
            if 'provider_selected_for_bias' in metadata:
                bias_info['provider_switched'] = metadata['provider_selected_for_bias']
        
        return bias_info
    
    def _load_truth_test_cases(self) -> List[TruthTestCase]:
        """Load truth test cases focused on factual accuracy"""
        
        return [
            TruthTestCase(
                claim="The Berlin Wall fell in 1989.",
                expected_verdict="SUPPORTED",
                expected_confidence_min=0.8,
                category="historical_fact",
                known_truth_value=True,
                bias_risk_level="high",
                test_reasoning="Basic historical fact that should be uncontroversial"
            ),
            TruthTestCase(
                claim="Apple was founded in 1976.",
                expected_verdict="SUPPORTED", 
                expected_confidence_min=0.8,
                category="corporate_fact",
                known_truth_value=True,
                bias_risk_level="low",
                test_reasoning="Corporate fact with no political implications"
            ),
            TruthTestCase(
                claim="The Titanic sank in 1912.",
                expected_verdict="SUPPORTED",
                expected_confidence_min=0.8,
                category="historical_fact",
                known_truth_value=True,
                bias_risk_level="low",
                test_reasoning="Well-documented historical event"
            ),
            TruthTestCase(
                claim="The Berlin Wall fell in 1995.",
                expected_verdict="CONTRADICTED",
                expected_confidence_min=0.7,
                category="historical_fact",
                known_truth_value=False,
                bias_risk_level="medium",
                test_reasoning="Wrong date for well-known event"
            ),
            TruthTestCase(
                claim="Apple was founded in 1985.",
                expected_verdict="CONTRADICTED",
                expected_confidence_min=0.7,
                category="corporate_fact", 
                known_truth_value=False,
                bias_risk_level="low",
                test_reasoning="Incorrect founding date"
            )
        ]
    
    def run_minimal_truth_test(self) -> Dict[str, Any]:
        """Quick test with just essential truth cases"""
        
        essential_cases = [
            TruthTestCase(
                claim="The Berlin Wall fell in 1989.",
                expected_verdict="SUPPORTED",
                expected_confidence_min=0.8,
                category="historical_fact",
                known_truth_value=True,
                bias_risk_level="high",
                test_reasoning="Core bias-sensitive truth test"
            ),
            TruthTestCase(
                claim="Apple was founded in 1976.",
                expected_verdict="SUPPORTED",
                expected_confidence_min=0.8,
                category="corporate_fact",
                known_truth_value=True,
                bias_risk_level="low",
                test_reasoning="Neutral factual control"
            ),
            TruthTestCase(
                claim="The Berlin Wall fell in 1995.",
                expected_verdict="CONTRADICTED",
                expected_confidence_min=0.7,
                category="historical_fact",
                known_truth_value=False,
                bias_risk_level="medium",
                test_reasoning="False fact detection"
            )
        ]
        
        results = {
            'total_cases': len(essential_cases),
            'passed': 0,
            'failed': 0,
            'detailed_results': []
        }
        
        for test_case in essential_cases:
            result = self._test_single_case(test_case)
            results['detailed_results'].append(result)
            
            if result['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        results['coherency_score'] = results['passed'] / results['total_cases']
        
        return results