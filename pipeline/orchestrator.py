# automated_skeptic_mvp/pipeline/orchestrator.py
"""
Pipeline orchestrator with parallel processing capabilities
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.herald_agent import HeraldAgent
from agents.illuminator_agent import IlluminatorAgent
from agents.logician_agent import LogicianAgent
from agents.seeker_agent import SeekerAgent
from agents.oracle_agent import OracleAgent
from data.models import Claim, VerificationResult
from config.settings import Settings

class SkepticPipeline:
    """Pipeline orchestrator with parallel processing and bias-aware routing"""
    
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        
        # Initialize agents
        self.herald = HeraldAgent()
        self.illuminator = IlluminatorAgent()
        self.logician = LogicianAgent(settings)
        self.seeker = SeekerAgent(settings)
        self.oracle = OracleAgent(settings)
        
        # Configuration
        self.enable_parallel = getattr(settings, 'get', lambda *args: 'false')('PHASE6', 'enable_parallel_processing', 'false').lower() == 'true'
        self.max_workers = getattr(settings, 'getint', lambda *args: 3)('PHASE6', 'max_parallel_workers', 3)
        
        self.logger.info(f"Pipeline initialized (parallel: {self.enable_parallel})")
    
    def process_claim(self, claim: Claim) -> VerificationResult:
        """Process claim through pipeline with parallel capabilities"""
        start_time = datetime.now()
        
        try:
            # Stage 1: Herald - Input validation (always sequential)
            self.logger.info("Stage 1: Herald processing")
            processed_claim = self.herald.process(claim.text)
            
            if not processed_claim:
                raise Exception("Herald rejected input as invalid")
            
            claim = processed_claim
            
            # Stages 2-4: Parallel or sequential processing
            if self.enable_parallel:
                claim = self._process_parallel_stages(claim)
            else:
                claim = self._process_sequential_stages(claim)
            
            # Stage 5: Oracle - Final analysis
            self.logger.info("Stage 5: Oracle processing")
            result = self.oracle.process(claim)
            
            total_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = total_time
            
            # Add metadata
            if not hasattr(result, 'metadata'):
                result.metadata = {}
            result.metadata.update({
                'pipeline_version': 'v2',
                'parallel_processing': self.enable_parallel,
                'total_processing_time': total_time
            })
            
            self.logger.info(f"Pipeline completed in {total_time:.2f}s with verdict: {result.verdict}")
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline processing error: {str(e)}")
            
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
    
    def _process_parallel_stages(self, claim: Claim) -> Claim:
        """Process stages 2-4 in parallel where possible"""
        self.logger.info("Processing stages 2-4 in parallel mode")
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Stage 2: Illuminator (can run independently)
                illuminator_future = executor.submit(self._safe_illuminator_process, claim)
                
                # Wait for illuminator to complete
                claim = illuminator_future.result(timeout=60)
                
                # Stage 3: Logician (needs illuminator results)
                logician_future = executor.submit(self._safe_logician_process, claim)
                claim = logician_future.result(timeout=120)
                
                # Stage 4: Seeker (needs sub-claims from logician)
                seeker_future = executor.submit(self._safe_seeker_process, claim)
                claim = seeker_future.result(timeout=180)
                
        except Exception as e:
            self.logger.warning(f"Parallel processing failed, falling back to sequential: {str(e)}")
            claim = self._process_sequential_stages(claim)
        
        return claim
    
    def _process_sequential_stages(self, claim: Claim) -> Claim:
        """Process stages 2-4 sequentially"""
        self.logger.info("Processing stages 2-4 in sequential mode")
        
        # Stage 2: Illuminator
        self.logger.info("Stage 2: Illuminator processing")
        claim = self.illuminator.process(claim)
        
        # Stage 3: Logician
        self.logger.info("Stage 3: Logician processing")
        claim = self.logician.process(claim)
        
        # Stage 4: Seeker
        self.logger.info("Stage 4: Seeker processing")
        claim = self.seeker.process(claim)
        
        return claim
    
    def _safe_illuminator_process(self, claim: Claim) -> Claim:
        """Safe wrapper for illuminator processing"""
        try:
            return self.illuminator.process(claim)
        except Exception as e:
            self.logger.error(f"Illuminator processing failed: {str(e)}")
            return claim
    
    def _safe_logician_process(self, claim: Claim) -> Claim:
        """Safe wrapper for logician processing"""
        try:
            return self.logician.process(claim)
        except Exception as e:
            self.logger.error(f"Logician processing failed: {str(e)}")
            # Ensure we have at least one sub-claim
            if not hasattr(claim, 'sub_claims') or not claim.sub_claims:
                from data.models import SubClaim
                claim.sub_claims = [SubClaim(
                    text=claim.text,
                    verifiable=True
                )]
            return claim
    
    def _safe_seeker_process(self, claim: Claim) -> Claim:
        """Safe wrapper for seeker processing"""
        try:
            return self.seeker.process(claim)
        except Exception as e:
            self.logger.error(f"Seeker processing failed: {str(e)}")
            # Ensure we have sources attribute
            if not hasattr(claim, 'sources'):
                claim.sources = []
            return claim
    
    def process_multiple_claims(self, claims: List[Claim], batch_size: int = 5) -> List[VerificationResult]:
        """Process multiple claims with optional batching"""
        self.logger.info(f"Processing {len(claims)} claims in batches of {batch_size}")
        
        results = []
        
        if self.enable_parallel and len(claims) > 1:
            # Process claims in parallel batches
            for i in range(0, len(claims), batch_size):
                batch = claims[i:i + batch_size]
                batch_results = self._process_claim_batch_parallel(batch)
                results.extend(batch_results)
        else:
            # Process claims sequentially
            for i, claim in enumerate(claims):
                self.logger.info(f"Processing claim {i+1}/{len(claims)}")
                result = self.process_claim(claim)
                results.append(result)
        
        return results
    
    def _process_claim_batch_parallel(self, claims: List[Claim]) -> List[VerificationResult]:
        """Process a batch of claims in parallel"""
        results = []
        
        try:
            with ThreadPoolExecutor(max_workers=min(len(claims), self.max_workers)) as executor:
                # Submit all claims for processing
                future_to_claim = {
                    executor.submit(self.process_claim, claim): claim 
                    for claim in claims
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_claim, timeout=300):
                    claim = future_to_claim[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Parallel claim processing failed for '{claim.text}': {str(e)}")
                        # Create error result
                        error_result = VerificationResult(
                            original_claim=claim.text,
                            verdict="ERROR",
                            confidence=0.0,
                            evidence_summary=f"Parallel processing error: {str(e)}",
                            sources=[],
                            processing_time=0.0,
                            error_message=str(e)
                        )
                        results.append(error_result)
        
        except Exception as e:
            self.logger.error(f"Batch parallel processing failed: {str(e)}")
            # Fallback to sequential processing
            for claim in claims:
                result = self.process_claim(claim)
                results.append(result)
        
        return results
    
    def get_pipeline_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the pipeline"""
        
        return {
            'pipeline_version': 'v2',
            'parallel_processing_enabled': self.enable_parallel,
            'max_parallel_workers': self.max_workers,
            'agents': {
                'herald': {'type': 'HeraldAgent', 'status': 'active'},
                'illuminator': {'type': 'IlluminatorAgent', 'status': 'active'},
                'logician': {'type': 'LogicianAgent', 'status': 'active'},
                'seeker': {'type': 'SeekerAgent', 'status': 'active'},
                'oracle': {'type': 'OracleAgent', 'status': 'active'}
            }
        }
    
    def validate_pipeline_configuration(self) -> Dict[str, Any]:
        """Validate pipeline configuration and component availability"""
        validation_results = {
            'overall_status': 'healthy',
            'issues': [],
            'warnings': [],
            'agent_status': {}
        }
        
        # Validate each agent
        agents = {
            'herald': self.herald,
            'illuminator': self.illuminator,
            'logician': self.logician,
            'seeker': self.seeker,
            'oracle': self.oracle
        }
        
        for agent_name, agent in agents.items():
            try:
                # Basic validation
                required_methods = ['process']
                agent_status = {
                    'available': True,
                    'methods': all(hasattr(agent, method) for method in required_methods)
                }
                
                # Special validation for LLM-enabled agents
                if hasattr(agent, 'has_llm'):
                    agent_status['llm_available'] = agent.has_llm
                    if not agent.has_llm:
                        validation_results['warnings'].append(f"{agent_name} has no LLM available")
                
                validation_results['agent_status'][agent_name] = agent_status
                
            except Exception as e:
                validation_results['issues'].append(f"{agent_name} validation failed: {str(e)}")
                validation_results['agent_status'][agent_name] = {
                    'available': False,
                    'error': str(e)
                }
        
        # Check configuration consistency
        if self.enable_parallel and self.max_workers < 2:
            validation_results['warnings'].append("Parallel processing enabled but max_workers < 2")
        
        # Overall status
        if validation_results['issues']:
            validation_results['overall_status'] = 'degraded'
        elif validation_results['warnings']:
            validation_results['overall_status'] = 'warning'
        
        return validation_results