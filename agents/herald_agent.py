# automated_skeptic_mvp/agents/herald_agent.py
"""
Input Agent (The Herald) - Handles text cleaning, normalization, and input validation
"""

import re
import logging
from typing import Optional
from data.models import Claim

class HeraldAgent:
    """Input processing and validation agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Common patterns for basic validation
        self.min_length = 10
        self.max_length = 1000
        
    def process(self, raw_text: str) -> Optional[Claim]:
        """
        Process raw input text into a clean Claim object
        
        Args:
            raw_text: Raw input text to process
            
        Returns:
            Claim object if valid, None if invalid
        """
        try:
            # Step 1: Basic validation
            if not self._validate_input(raw_text):
                return None
            
            # Step 2: Clean and normalize text
            cleaned_text = self._clean_text(raw_text)
            
            # Step 3: Create claim object
            claim = Claim(text=cleaned_text)
            
            self.logger.info(f"Herald processed claim: '{cleaned_text[:50]}...'")
            return claim
            
        except Exception as e:
            self.logger.error(f"Herald processing error: {str(e)}")
            return None
    
    def _validate_input(self, text: str) -> bool:
        """Validate input text meets basic requirements"""
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid input: empty or non-string")
            return False
        
        if len(text.strip()) < self.min_length:
            self.logger.warning(f"Input too short: {len(text.strip())} chars")
            return False
        
        if len(text) > self.max_length:
            self.logger.warning(f"Input too long: {len(text)} chars")
            return False
        
        # Check for obviously invalid content
        if self._contains_only_symbols(text):
            self.logger.warning("Input contains only symbols/numbers")
            return False
        
        return True
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove or normalize special characters
        cleaned = re.sub(r'[""''„‚]', '"', cleaned)  # Normalize quotes
        cleaned = re.sub(r'[–—]', '-', cleaned)  # Normalize dashes
        
        # Remove non-printable characters
        cleaned = ''.join(char for char in cleaned if char.isprintable() or char.isspace())
        
        # Ensure proper sentence ending
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def _contains_only_symbols(self, text: str) -> bool:
        """Check if text contains only symbols and numbers without meaningful words"""
        # Remove all non-alphabetic characters and check if anything remains
        alpha_only = re.sub(r'[^a-zA-Z]', '', text)
        return len(alpha_only) < 3  # Need at least 3 letters for meaningful content
