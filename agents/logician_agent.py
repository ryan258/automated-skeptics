# automated_skeptic_mvp/agents/logician_agent.py
"""
Deconstruction Agent (The Logician) - Enhanced with flexible LLM support
"""

import logging
import re
from typing import List, Dict, Any
from llm.manager import LLMManager
from llm.base import LLMMessage
from data.models import Claim, SubClaim, Entity, ClaimType
from config.settings import Settings

class LogicianAgent:
    """Claim deconstruction and logical analysis agent with flexible LLM support"""
    
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.agent_name = "logician"
        
        # Initialize LLM manager
        self.llm_manager = LLMManager(settings)
        
        # Check if we have any LLM available
        self.has_llm = len(self.llm_manager.get_available_providers()) > 0
        
        if self.has_llm:
            provider_info = self.llm_manager.get_available_providers()
            self.logger.info(f"Logician initialized with LLM providers: {list(provider_info.keys())}")
        else:
            self.logger.warning("No LLM providers available. Using rule-based processing only.")
    
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
            if self.has_llm:
                sub_claims = self._llm_deconstruct_claim(claim.text)
            else:
                sub_claims = self._rule_based_deconstruct(claim)
            
            claim.sub_claims = sub_claims
            
            self.logger.info(f"Logician identified {len(sub_claims)} sub-claims using {'LLM' if self.has_llm else 'rule-based'} processing")
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
            # Create system message with instructions
            system_message = LLMMessage(
                role="system",
                content="""You are an expert at breaking down factual claims into verifiable sub-components. 
Your task is to identify specific, independently verifiable facts from complex claims.

Focus on:
1. Key factual assertions that can be independently verified
2. Entities involved (people, organizations, dates, locations)
3. Relationships between entities
4. Claims that can be checked against reliable sources

Return your analysis in this exact format:
SUB-CLAIM 1: [specific verifiable fact]
ENTITIES: [entity1], [entity2], [entity3]

SUB-CLAIM 2: [another specific verifiable fact]  
ENTITIES: [entity1], [entity2]

Only include claims that can be verified through reliable sources."""
            )
            
            # Create user message with the claim
            user_message = LLMMessage(
                role="user",
                content=f"Break down this claim into verifiable sub-components:\n\nClaim: \"{claim_text}\""
            )
            
            # Get LLM response
            response = self.llm_manager.generate(
                messages=[system_message, user_message],
                agent_name=self.agent_name,
                temperature=0.1,
                max_tokens=600
            )
            
            # Log LLM usage for cost tracking
            if response.usage:
                self.logger.info(f"LLM usage - Provider: {response.provider.value}, "
                               f"Model: {response.model}, "
                               f"Tokens: {response.usage.get('total_tokens', 'unknown')}, "
                               f"Cost: ${response.usage.get('estimated_cost', 0):.4f}")
            
            return self._parse_llm_response(response.content, claim_text)
            
        except Exception as e:
            self.logger.error(f"LLM deconstruction failed: {str(e)}")
            return self._rule_based_deconstruct_simple(claim_text)
    
    def _parse_llm_response(self, response_text: str, original_claim: str) -> List[SubClaim]:
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
                parts = line.split(':', 1)
                if len(parts) > 1:
                    current_claim = parts[1].strip()
                    current_entities = []
                
            elif line.startswith('ENTITIES:') and current_claim:
                # Extract entities
                parts = line.split(':', 1)
                if len(parts) > 1:
                    entities_text = parts[1].strip()
                    entity_names = [e.strip() for e in entities_text.split(',') if e.strip()]
                    
                    for entity_name in entity_names:
                        current_entities.append(Entity(
                            text=entity_name,
                            entity_type="LLM_EXTRACTED",
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
        
        # If no sub-claims were extracted, create one from the original
        if not sub_claims:
            sub_claims = [SubClaim(
                text=original_claim,
                verifiable=True
            )]
        
        return sub_claims
    
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
            for date_entity in date_entities:
                # Extract the event part (everything except the date)
                event_text = claim.text.replace(date_entity.text, "").strip()
                event_text = re.sub(r'\s+', ' ', event_text)  # Clean whitespace
                
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
        # For biographical facts, we can often separate person identity from the fact
        person_entities = [e for e in claim.entities if e.entity_type in ["PERSON", "ORG"]]
        
        if person_entities:
            # Create separate sub-claims for person existence and the specific fact
            sub_claims = []
            
            for person in person_entities:
                # Sub-claim 1: Person exists/existed
                sub_claims.append(SubClaim(
                    text=f"{person.text} is a real person/entity",
                    entities=[person],
                    claim_type=ClaimType.BIOGRAPHICAL_FACT,
                    verifiable=True
                ))
            
            # Sub-claim 2: The specific biographical fact
            sub_claims.append(SubClaim(
                text=claim.text,
                entities=claim.entities,
                claim_type=claim.claim_type,
                verifiable=True
            ))
            
            return sub_claims
        
        # Fallback to single claim
        return [SubClaim(
            text=claim.text,
            entities=claim.entities,
            claim_type=claim.claim_type,
            verifiable=True
        )]
    
    def _deconstruct_corporate_fact(self, claim: Claim) -> List[SubClaim]:
        """Deconstruct corporate fact claims"""
        # Similar to biographical facts but for organizations
        org_entities = [e for e in claim.entities if e.entity_type == "ORG"]
        
        if org_entities:
            sub_claims = []
            
            for org in org_entities:
                # Sub-claim 1: Organization exists
                sub_claims.append(SubClaim(
                    text=f"{org.text} is a real organization",
                    entities=[org],
                    claim_type=ClaimType.CORPORATE_FACT,
                    verifiable=True
                ))
            
            # Sub-claim 2: The specific corporate fact
            sub_claims.append(SubClaim(
                text=claim.text,
                entities=claim.entities,
                claim_type=claim.claim_type,
                verifiable=True
            ))
            
            return sub_claims
        
        # Fallback to single claim
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
    
    def get_llm_info(self) -> Dict[str, Any]:
        """Get information about the LLM configuration for this agent"""
        if not self.has_llm:
            return {"status": "no_llm", "provider": None}
        
        provider_name = self.llm_manager.get_provider_for_agent(self.agent_name)
        providers = self.llm_manager.get_available_providers()
        
        return {
            "status": "available",
            "assigned_provider": provider_name,
            "provider_info": providers.get(provider_name, {}),
            "all_providers": providers
        }