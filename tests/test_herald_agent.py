# automated_skeptic_mvp/tests/test_herald_agent.py
"""
Unit tests for Herald Agent
"""

import pytest
from agents.herald_agent import HeraldAgent
from data.models import Claim

class TestHeraldAgent:
    """Test cases for Herald Agent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.herald = HeraldAgent()
    
    def test_valid_claim_processing(self):
        """Test processing of valid claims"""
        test_claim = "The Berlin Wall fell in 1989."
        
        result = self.herald.process(test_claim)
        
        assert result is not None
        assert isinstance(result, Claim)
        assert result.text == "The Berlin Wall fell in 1989."
    
    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        messy_text = "  The   Berlin  Wall fell    in 1989  "
        
        result = self.herald.process(messy_text)
        
        assert result is not None
        assert result.text == "The Berlin Wall fell in 1989."
    
    def test_sentence_ending_addition(self):
        """Test automatic addition of sentence ending"""
        no_ending = "The Berlin Wall fell in 1989"
        
        result = self.herald.process(no_ending)
        
        assert result is not None
        assert result.text.endswith(".")
    
    def test_empty_input_rejection(self):
        """Test rejection of empty input"""
        result = self.herald.process("")
        assert result is None
        
        result = self.herald.process("   ")
        assert result is None
    
    def test_too_short_input_rejection(self):
        """Test rejection of too short input"""
        short_text = "Hi"
        
        result = self.herald.process(short_text)
        
        assert result is None
    
    def test_too_long_input_rejection(self):
        """Test rejection of too long input"""
        long_text = "A" * 1001  # Exceeds max length
        
        result = self.herald.process(long_text)
        
        assert result is None
    
    def test_symbols_only_rejection(self):
        """Test rejection of symbol-only input"""
        symbols_text = "!@#$%^&*()123456"
        
        result = self.herald.process(symbols_text)
        
        assert result is None
