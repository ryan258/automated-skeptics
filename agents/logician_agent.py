# automated_skeptic_mvp/agents/logician_agent.py
"""
Deconstruction Agent (The Logician) - Core claim parsing and entity extraction
"""

import logging
import re
from typing import List, Dict, Any
import openai

from data.models import Claim, SubClaim, Entity, ClaimType
from config.settings import Settings

class LogicianAgent:
    """Claim deconstruction and logical analysis agent"""
    
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        
        # Configure OpenAI if API key is available
        api_key = settings.get('API_KEYS', 'openai_api_key')
        if api_key:
            openai.api_key = api_key
            self.use_llm = True
        else:
            self.logger.warning("OpenAI API key not found. Using rule-based deconstruction.")
            self.use_llm = False
    
    def process(self, claim: Claim) -> Claim:
        """
        Deconstruct claim into verifiable sub-components
        
        Args:
            claim: Claim object to deconstruct
            
        Returns:
            Enhanced claim with sub-claims identified
        """
        try:
            # Deconstruct claim into sub-claims
            if self.use_llm:
                sub_claims = self._llm_deconstruct_claim(claim.text)
            else:
                sub_claims = self._rule_based_deconstruct(claim)
            
            claim.sub_claims = sub_claims
            
            self.logger.info(f"Logician identified {len(sub_claims)} sub-claims")
            return claim
            
        except Exception as e:
            self.logger.error(f"Logician processing error: {str(e)}")
            # Create a fallback sub-claim with the original text
            claim.sub_claims = [SubClaim(
                text=claim.text,
                claim_type=claim.claim_type,
                verifiable=True
            )]
            return claim
    
    def _llm_deconstruct_claim(self, claim_text: str) -> List[SubClaim]:
        """Use LLM to deconstruct claim into verifiable components"""
        try:
            prompt = self._create_deconstruction_prompt(claim_text)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at breaking down factual claims into verifiable sub-components."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return self._parse_llm_response(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"LLM deconstruction failed: {str(e)}")
            return self._rule_based_deconstruct_simple(claim_text)
    
    def _create_deconstruction_prompt(self, claim_text: str) -> str:
        """Create prompt for LLM-based claim deconstruction"""
        return f"""
        Break down the following claim into its verifiable sub-components:
        
        Claim: "{claim_text}"
        
        Please identify:
        1. Key factual assertions that can be independently verified
        2. Entities involved (people, organizations, dates, locations)
        3. Relationships between entities
        
        Format your response as:
        SUB-CLAIM 1: [specific verifiable fact]
        ENTITIES: [entity1], [entity2], ...
        
        SUB-CLAIM 2: [another specific verifiable fact]
        ENTITIES: [entity1], [entity2], ...
        
        Focus on claims that can be verified through reliable sources.
        """
    
    def _parse_llm_response(self, response_text: str) -> List[SubClaim]:
        """Parse LLM response into SubClaim objects"""
        sub_claims = []
        current_claim = None
        current_entities = []
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUB-CLAIM'):
                # Save previous claim if exists
                if current_claim:
                    sub_claims.append(SubClaim(
                        text=current_claim,
                        entities=current_entities,
                        verifiable=True
                    ))
                
                # Extract new claim text
                current_claim = line.split(':', 1)[1].strip()
                current_entities = []
                
            elif line.startswith('ENTITIES:'):
                # Extract entities
                entities_text = line.split(':', 1)[1].strip()
                entity_names = [e.strip() for e in entities_text.split(',') if e.strip()]
                
                for i, entity_name in enumerate(entity_names):
                    current_entities.append(Entity(
                        text=entity_name,
                        entity_type="UNKNOWN",
                        start_pos=0,  # Position would need to be calculated
                        end_pos=len(entity_name),
                        confidence=0.8
                    ))
        
        # Add the last claim
        if current_claim:
            sub_claims.append(SubClaim(
                text=current_claim,
                entities=current_entities,
                verifiable=True
            ))
        
        return sub_claims if sub_claims else self._rule_based_deconstruct_simple(current_claim or "")
    
    def _rule_based_deconstruct(self, claim: Claim) -> List[SubClaim]:
        """Rule-based claim deconstruction for when LLM is not available"""
        sub_claims = []
        
        # Based on claim type, apply different deconstruction strategies
        if claim.claim_type == ClaimType.HISTORICAL_DATE:
            sub_claims.extend(self._deconstruct_historical_date(claim))
        elif claim.claim_type == ClaimType.BIOGRAPHICAL_FACT:
            sub_claims.extend(self._deconstruct_biographical_fact(claim))
        elif claim.claim_type == ClaimType.CORPORATE_FACT:
            sub_claims.extend(self._deconstruct_corporate_fact(claim))
        else:
            # Generic deconstruction
            sub_claims.append(SubClaim(
                text=claim.text,
                entities=claim.entities,
                claim_type=claim.claim_type,
                verifiable=True
            ))
        
        return sub_claims
    
    def _deconstruct_historical_date(self, claim: Claim) -> List[SubClaim]:
        """Deconstruct historical date claims"""
        sub_claims = []
        
        # Look for event + date pattern
        date_entities = [e for e in claim.entities if e.entity_type == "DATE"]
        
        if date_entities:
            # Create sub-claim for the event occurrence
            event_text = claim.text
            for date_entity in date_entities:
                sub_claim_text = f"The event '{event_text}' occurred in {date_entity.text}"
                sub_claims.append(SubClaim(
                    text=sub_claim_text,
                    entities=[date_entity],
                    claim_type=ClaimType.HISTORICAL_DATE,
                    verifiable=True
                ))
        else:
            # Fallback to original claim
            sub_claims.append(SubClaim(
                text=claim.text,
                entities=claim.entities,
                claim_type=claim.claim_type,
                verifiable=True
            ))
        
        return sub_claims
    
    def _deconstruct_biographical_fact(self, claim: Claim) -> List[SubClaim]:
        """Deconstruct biographical fact claims"""
        # For now, treat as single verifiable claim
        return [SubClaim(
            text=claim.text,
            entities=claim.entities,
            claim_type=claim.claim_type,
            verifiable=True
        )]
    
    def _deconstruct_corporate_fact(self, claim: Claim) -> List[SubClaim]:
        """Deconstruct corporate fact claims"""
        # For now, treat as single verifiable claim
        return [SubClaim(
            text=claim.text,
            entities=claim.entities,
            claim_type=claim.claim_type,
            verifiable=True
        )]
    
    def _rule_based_deconstruct_simple(self, claim_text: str) -> List[SubClaim]:
        """Simple fallback deconstruction"""
        return [SubClaim(
            text=claim_text,
            verifiable=True
        )]
