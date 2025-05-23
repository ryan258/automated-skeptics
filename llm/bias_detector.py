# automated_skeptic_mvp/llm/bias_detector.py
"""
Bias Detection Module for LLM Responses
"""

import re
import logging
from typing import Dict, List, Any

class BiasDetector:
    """Detects potential bias in content and LLM responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_bias_patterns()
    
    def _load_bias_patterns(self):
        """Load patterns that indicate potential bias"""
        self.political_keywords = [
            'berlin wall', 'tiananmen square', 'hong kong protests', 'taiwan independence',
            'tibet', 'xinjiang', 'uyghur', 'falun gong', 'democracy china',
            'human rights china', 'censorship china', 'cultural revolution'
        ]
        
        self.avoidance_phrases = [
            'insufficient information', 'cannot be verified', 'unclear from sources',
            'disputed claims', 'different perspectives', 'complex situation',
            'multiple viewpoints', 'sensitive topic', 'political nature'
        ]
    
    def analyze_content_bias_risk(self, content: str) -> Dict[str, Any]:
        """Analyze content for potential bias risk"""
        content_lower = content.lower()
        
        # Check for politically sensitive keywords
        sensitive_matches = 0
        for keyword in self.political_keywords:
            if keyword in content_lower:
                sensitive_matches += 1
        
        # Calculate risk score
        if sensitive_matches == 0:
            risk_score = 0.0
        else:
            # High risk patterns
            high_risk_patterns = [
                'berlin wall.*1989', 'tiananmen.*1989', 'hong kong.*protest'
            ]
            
            for pattern in high_risk_patterns:
                if re.search(pattern, content_lower):
                    risk_score = 0.8
                    break
            else:
                risk_score = min(sensitive_matches * 0.3, 0.7)
        
        return {
            'overall_score': risk_score,
            'categories': ['political'] if risk_score > 0.3 else [],
            'high_risk': risk_score > 0.7,
            'requires_safe_provider': risk_score > 0.5
        }
    
    def analyze_response_bias(self, original_content: str, response: str) -> Dict[str, Any]:
        """Analyze LLM response for bias patterns"""
        response_lower = response.lower()
        original_lower = original_content.lower()
        
        bias_score = 0.0
        
        # Check for avoidance patterns
        avoidance_score = self._check_avoidance_patterns(response_lower, original_lower)
        bias_score = max(bias_score, avoidance_score)
        
        # Check for factual omissions
        omission_score = self._check_factual_omissions(original_lower, response_lower)
        bias_score = max(bias_score, omission_score)
        
        return {
            'bias_score': bias_score,
            'bias_level': self._categorize_bias_level(bias_score),
            'avoidance_score': avoidance_score,
            'omission_score': omission_score,
            'is_biased': bias_score > 0.6
        }
    
    def _check_avoidance_patterns(self, response: str, original: str) -> float:
        """Check for avoidance patterns in response"""
        avoidance_score = 0.0
        
        # Berlin Wall specific check
        if 'berlin wall' in original and '1989' in original:
            for phrase in self.avoidance_phrases:
                if phrase in response:
                    avoidance_score = max(avoidance_score, 0.9)
                    break
            
            # Check if response avoids confirming the fact
            confirmation_words = ['fell', 'fall', 'collapsed', 'ended', 'demolished']
            has_confirmation = any(word in response for word in confirmation_words)
            
            if not has_confirmation and len(response) > 50:
                avoidance_score = max(avoidance_score, 0.8)
        
        return avoidance_score
    
    def _check_factual_omissions(self, original: str, response: str) -> float:
        """Check for suspicious factual omissions"""
        omission_score = 0.0
        
        # Berlin Wall case: should mention the date
        if 'berlin wall' in original and 'fell' in original:
            if '1989' not in response and 'november' not in response:
                omission_score = max(omission_score, 0.7)
        
        return omission_score
    
    def _categorize_bias_level(self, score: float) -> str:
        """Categorize bias level based on score"""
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.6:
            return "MEDIUM"
        elif score >= 0.3:
            return "LOW"
        else:
            return "MINIMAL"