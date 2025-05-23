# automated_skeptic_mvp/tests/test_pipeline.py
"""
Integration tests for the complete pipeline
"""

import pytest
from pipeline.orchestrator import SkepticPipeline
from data.models import Claim
from config.settings import Settings

class TestSkepticPipeline:
    """Test cases for the complete pipeline"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create test settings
        self.settings = Settings("config/test_config.ini")
        self.pipeline = SkepticPipeline(self.settings)
    
    def test_simple_claim_processing(self):
        """Test processing of a simple claim"""
        claim = Claim(text="The Berlin Wall fell in 1989.")
        
        result = self.pipeline.process_claim(claim)
        
        assert result is not None
        assert result.original_claim == "The Berlin Wall fell in 1989."
        assert result.verdict in ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "ERROR"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time > 0
    
    def test_invalid_claim_handling(self):
        """Test handling of invalid claims"""
        claim = Claim(text="")
        
        result = self.pipeline.process_claim(claim)
        
        assert result is not None
        assert result.verdict == "ERROR"
        assert result.confidence == 0.0
    
    def test_processing_time_measurement(self):
        """Test that processing time is measured"""
        claim = Claim(text="Apple was founded in 1976.")
        
        result = self.pipeline.process_claim(claim)
        
        assert result.processing_time > 0
