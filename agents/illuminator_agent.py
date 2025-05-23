# automated_skeptic_mvp/agents/illuminator_agent.py
"""
Context Agent (The Illuminator) - Simplified version for MVP
Handles basic topic classification and entity recognition
"""

import re
import logging
from typing import List, Optional
from datetime import datetime
import spacy

from data.models import Claim, ClaimType, Entity

class IlluminatorAgent:
    """Context analysis and topic classification agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_nlp_model()
        
        # Pattern matching for basic classification
        self.date_patterns = [
            r'\b\d{4}\b',  # Year patterns
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}\b'
        ]
        
        self.biographical_keywords = [
            'born', 'birth', 'died', 'death', 'lived', 'age', 'married', 'graduated',
            'studied', 'worked', 'served', 'became', 'appointed', 'elected'
        ]
        
        self.corporate_keywords = [
            'founded', 'established', 'company', 'corporation', 'business', 'startup',
            'IPO', 'acquired', 'merger', 'revenue', 'profit', 'headquarters'
        ]
        
        self.news_keywords = [
            'announced', 'reported', 'happened', 'occurred', 'event', 'incident',
            'today', 'yesterday', 'recently', 'breaking'
        ]
    
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            self.logger.warning("spaCy model 'en_core_web_sm' not found. Using basic processing.")
            self.nlp = None
    
    def process(self, claim: Claim) -> Claim:
        """
        Analyze claim context and classify topic
        
        Args:
            claim: Claim object to analyze
            
        Returns:
            Enhanced claim with context information
        """
        try:
            # Classify claim type
            claim.claim_type = self._classify_claim_type(claim.text)
            
            # Extract entities
            claim.entities = self._extract_entities(claim.text)
            
            self.logger.info(f"Illuminator classified claim as: {claim.claim_type.value}")
            return claim
            
        except Exception as e:
            self.logger.error(f"Illuminator processing error: {str(e)}")
            claim.claim_type = ClaimType.UNKNOWN
            return claim
    
    def _classify_claim_type(self, text: str) -> ClaimType:
        """Classify the type of claim based on content analysis"""
        text_lower = text.lower()
        
        # Check for historical dates
        if any(re.search(pattern, text) for pattern in self.date_patterns):
            if any(keyword in text_lower for keyword in self.biographical_keywords):
                return ClaimType.BIOGRAPHICAL_FACT
            elif any(keyword in text_lower for keyword in self.corporate_keywords):
                return ClaimType.CORPORATE_FACT
            else:
                return ClaimType.HISTORICAL_DATE
        
        # Check for biographical content
        if any(keyword in text_lower for keyword in self.biographical_keywords):
            return ClaimType.BIOGRAPHICAL_FACT
        
        # Check for corporate content
        if any(keyword in text_lower for keyword in self.corporate_keywords):
            return ClaimType.CORPORATE_FACT
        
        # Check for news events
        if any(keyword in text_lower for keyword in self.news_keywords):
            return ClaimType.NEWS_EVENT
        
        return ClaimType.UNKNOWN
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text"""
        entities = []
        
        if self.nlp:
            # Use spaCy for entity extraction
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append(Entity(
                    text=ent.text,
                    entity_type=ent.label_,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    confidence=0.8  # Default confidence for spaCy entities
                ))
        else:
            # Fallback: basic pattern-based entity extraction
            entities.extend(self._extract_dates(text))
            entities.extend(self._extract_organizations(text))
        
        return entities
    
    def _extract_dates(self, text: str) -> List[Entity]:
        """Extract date entities using pattern matching"""
        entities = []
        
        # Year extraction
        for match in re.finditer(r'\b\d{4}\b', text):
            year = int(match.group())
            if 1000 <= year <= datetime.now().year + 10:  # Reasonable year range
                entities.append(Entity(
                    text=match.group(),
                    entity_type="DATE",
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.7
                ))
        
        return entities
    
    def _extract_organizations(self, text: str) -> List[Entity]:
        """Extract organization entities using pattern matching"""
        entities = []
        
        # Simple capitalized word sequences that might be organizations
        pattern = r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:Inc|Corp|Company|Corporation|Ltd|LLC)\b'
        
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                entity_type="ORG",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.6
            ))
        
        return entities
