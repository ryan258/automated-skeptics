# automated_skeptic_mvp/pipeline/orchestrator.py
"""
Pipeline orchestrator - coordinates all agents in the verification process
"""

import logging
from typing import Optional
from datetime import datetime

from agents.herald_agent import HeraldAgent
from agents.illuminator_agent import IlluminatorAgent
from agents.logician_agent import LogicianAgent
from agents.seeker_agent import SeekerAgent
from agents.oracle_agent import OracleAgent
from data.models import Claim, VerificationResult
from config.settings import Settings

class SkepticPipeline:
    """Main pipeline orchestrator for the Automated Skeptic system"""
    
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        
        # Initialize all agents
        self.herald = HeraldAgent()
        self.illuminator = IlluminatorAgent()
        self.logician = LogicianAgent(settings)
        self.seeker = SeekerAgent(settings)
        self.oracle = OracleAgent(settings)
        
        self.logger.info("SkepticPipeline initialized with all agents")
    
    def process_claim(self, claim: Claim) -> VerificationResult:
        """
        Process a claim through the complete verification pipeline
        
        Args:
            claim: Claim object to process
            
        Returns:
            VerificationResult with verdict and evidence
        """
        start_time = datetime.now()
        
        try:
            # Stage 1: Herald - Input validation and cleaning
            self.logger.info("Stage 1: Herald processing")
            processed_claim = self.herald.process(claim.text)
            
            if not processed_claim:
                raise Exception("Herald rejected input as invalid")
            
            # Use the processed claim
            claim = processed_claim
            
            # Stage 2: Illuminator - Context analysis and classification
            self.logger.info("Stage 2: Illuminator processing")
            claim = self.illuminator.process(claim)
            
            # Stage 3: Logician - Claim deconstruction
            self.logger.info("Stage 3: Logician processing")
            claim = self.logician.process(claim)
            
            # Stage 4: Seeker - Research and evidence gathering
            self.logger.info("Stage 4: Seeker processing")
            claim = self.seeker.process(claim)
            
            # Stage 5: Oracle - Evidence synthesis and verdict
            self.logger.info("Stage 5: Oracle processing")
            result = self.oracle.process(claim)
            
            total_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = total_time
            
            self.logger.info(f"Pipeline completed in {total_time:.2f}s with verdict: {result.verdict}")
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline processing error: {str(e)}")
            
            # Create error result
            total_time = (datetime.now() - start_time).total_seconds()
            
            return VerificationResult(
                original_claim=claim.text if claim else "Unknown claim",
                verdict="ERROR",
                confidence=0.0,
                evidence_summary=f"Pipeline error: {str(e)}",
                sources=[],
                processing_time=total_time,
                error_message=str(e)
            )
