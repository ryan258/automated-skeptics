# automated_skeptic_mvp/tests/test_illuminator_agent.py
"""
Unit tests for Illuminator Agent
"""

import pytest
from agents.illuminator_agent import IlluminatorAgent
from data.models import Claim, ClaimType

class TestIlluminatorAgent:
    """Test cases for Illuminator Agent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.illuminator = IlluminatorAgent()
    
    def test_historical_date_classification(self):
        """Test classification of historical date claims"""
        claim = Claim(text="The Berlin Wall fell in 1989.")
        
        result = self.illuminator.process(claim)
        
        assert result.claim_type == ClaimType.HISTORICAL_DATE
    
    def test_biographical_fact_classification(self):
        """Test classification of biographical fact claims"""
        claim = Claim(text="Albert Einstein was born in Germany.")
        
        result = self.illuminator.process(claim)
        
        assert result.claim_type == ClaimType.BIOGRAPHICAL_FACT
    
    def test_corporate_fact_classification(self):
        """Test classification of corporate fact claims"""
        claim = Claim(text="Apple was founded in 1976.")
        
        result = self.illuminator.process(claim)
        
        assert result.claim_type == ClaimType.CORPORATE_FACT
    
    def test_entity_extraction(self):
        """Test entity extraction from claims"""
        claim = Claim(text="Apple was founded in 1976.")
        
        result = self.illuminator.process(claim)
        
        # Should extract year entity
        date_entities = [e for e in result.entities if e.entity_type == "DATE"]
        assert len(date_entities) > 0
        assert any("1976" in e.text for e in date_entities)
    
    def test_unknown_classification_fallback(self):
        """Test fallback to unknown classification"""
        claim = Claim(text="This is a random statement without clear category.")
        
        result = self.illuminator.process(claim)
        
        assert result.claim_type == ClaimType.UNKNOWN
