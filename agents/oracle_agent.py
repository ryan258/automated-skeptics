# automated_skeptic_mvp/agents/oracle_agent.py
"""
Synthesis Agent (The Oracle) - Basic evidence aggregation and verdict generation
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from data.models import Claim, Source, Evidence, VerificationResult, VerdictType

class OracleAgent:
    """Evidence synthesis and verdict generation agent"""
    
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.confidence_threshold = settings.getfloat('PROCESSING', 'confidence_threshold', 0.7)
    
    def process(self, claim: Claim) -> VerificationResult:
        """
        Synthesize evidence and generate final verdict
        
        Args:
            claim: Claim object with sources to analyze
            
        Returns:
            VerificationResult with verdict and confidence
        """
        start_time = datetime.now()
        
        try:
            # Get sources from claim
            sources = getattr(claim, 'sources', [])
            
            if not sources:
                return self._create_insufficient_evidence_result(claim, start_time)
            
            # Analyze evidence from sources
            evidence_list = self._extract_evidence(claim, sources)
            
            # Generate verdict based on evidence
            verdict, confidence = self._generate_verdict(evidence_list)
            
            # Create evidence summary
            evidence_summary = self._create_evidence_summary(evidence_list, verdict)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = VerificationResult(
                original_claim=claim.text,
                verdict=verdict.value,
                confidence=confidence,
                evidence_summary=evidence_summary,
                sources=sources,
                processing_time=processing_time
            )
            
            self.logger.info(f"Oracle verdict: {verdict.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Oracle processing error: {str(e)}")
            return self._create_error_result(claim, str(e), start_time)
    
    def _extract_evidence(self, claim: Claim, sources: List[Source]) -> List[Evidence]:
        """Extract evidence from sources"""
        evidence_list = []
        
        for source in sources:
            # Simple keyword matching to determine if source supports claim
            supporting_text = self._extract_supporting_text(claim.text, source.content)
            supports_claim = self._assess_support(claim.text, source.content)
            confidence = self._calculate_evidence_confidence(claim.text, source.content, source.credibility_score)
            
            evidence = Evidence(
                source=source,
                supporting_text=supporting_text,
                supports_claim=supports_claim,
                confidence=confidence,
                extraction_method="keyword_matching"
            )
            
            evidence_list.append(evidence)
        
        return evidence_list
    
    def _extract_supporting_text(self, claim: str, content: str) -> str:
        """Extract relevant text from source content"""
        if not content:
            return ""
        
        # Simple approach: find sentences containing claim keywords
        claim_words = set(claim.lower().split())
        sentences = content.split('.')
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = claim_words.intersection(sentence_words)
            
            # If sentence contains significant overlap with claim, include it
            if len(overlap) >= min(3, len(claim_words) * 0.3):
                relevant_sentences.append(sentence.strip())
        
        return '. '.join(relevant_sentences[:3])  # Limit to 3 sentences
    
    def _assess_support(self, claim: str, content: str) -> bool:
        """Assess if content supports the claim"""
        if not content:
            return False
        
        # Simple keyword-based assessment
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        # Look for exact matches or high overlap
        claim_words = set(claim_lower.split())
        content_words = set(content_lower.split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Also check for negation indicators
        negation_words = ['not', 'no', 'never', 'false', 'incorrect', 'wrong', 'untrue']
        has_negation = any(neg in content_lower for neg in negation_words)
        
        # Support if high overlap and no strong negation
        return overlap_ratio > 0.5 and not has_negation
    
    def _calculate_evidence_confidence(self, claim: str, content: str, credibility_score: float) -> float:
        """Calculate confidence in evidence"""
        if not content:
            return 0.0
        
        # Base confidence on keyword overlap
        claim_words = set(claim.lower().split())
        content_words = set(content.lower().split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Combine with source credibility
        confidence = (overlap_ratio * 0.6) + (credibility_score * 0.4)
        
        return min(confidence, 1.0)
    
    def _generate_verdict(self, evidence_list: List[Evidence]) -> tuple[VerdictType, float]:
        """Generate verdict based on evidence"""
        if not evidence_list:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        # Count supporting vs contradicting evidence
        supporting_evidence = [e for e in evidence_list if e.supports_claim]
        contradicting_evidence = [e for e in evidence_list if not e.supports_claim]
        
        # Calculate weighted scores
        supporting_score = sum(e.confidence * e.source.credibility_score for e in supporting_evidence)
        contradicting_score = sum(e.confidence * e.source.credibility_score for e in contradicting_evidence)
        
        total_score = supporting_score + contradicting_score
        
        if total_score == 0:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        support_ratio = supporting_score / total_score
        
        # Determine verdict based on ratio and confidence threshold
        if support_ratio >= 0.7:
            verdict = VerdictType.SUPPORTED
            confidence = min(support_ratio, 0.95)
        elif support_ratio <= 0.3:
            verdict = VerdictType.CONTRADICTED
            confidence = min(1 - support_ratio, 0.95)
        else:
            verdict = VerdictType.INSUFFICIENT_EVIDENCE
            confidence = 0.5
        
        return verdict, confidence
    
    def _create_evidence_summary(self, evidence_list: List[Evidence], verdict: VerdictType) -> str:
        """Create human-readable evidence summary"""
        if not evidence_list:
            return "No evidence found to evaluate this claim."
        
        supporting_count = len([e for e in evidence_list if e.supports_claim])
        contradicting_count = len(evidence_list) - supporting_count
        
        summary_parts = []
        
        # Verdict explanation
        if verdict == VerdictType.SUPPORTED:
            summary_parts.append(f"This claim is SUPPORTED by the available evidence.")
        elif verdict == VerdictType.CONTRADICTED:
            summary_parts.append(f"This claim is CONTRADICTED by the available evidence.")
        else:
            summary_parts.append(f"There is INSUFFICIENT EVIDENCE to verify this claim.")
        
        # Evidence breakdown
        summary_parts.append(f"Found {len(evidence_list)} sources: {supporting_count} supporting, {contradicting_count} contradicting.")
        
        # Key supporting evidence
        if supporting_count > 0:
            supporting_evidence = [e for e in evidence_list if e.supports_claim]
            best_supporting = max(supporting_evidence, key=lambda e: e.confidence)
            summary_parts.append(f"Strongest supporting evidence: {best_supporting.supporting_text[:200]}...")
        
        return " ".join(summary_parts)
    
    def _create_insufficient_evidence_result(self, claim: Claim, start_time: datetime) -> VerificationResult:
        """Create result for insufficient evidence"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VerificationResult(
            original_claim=claim.text,
            verdict=VerdictType.INSUFFICIENT_EVIDENCE.value,
            confidence=0.0,
            evidence_summary="No sources found to evaluate this claim.",
            sources=[],
            processing_time=processing_time
        )
    
    def _create_error_result(self, claim: Claim, error_message: str, start_time: datetime) -> VerificationResult:
        """Create result for processing errors"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return VerificationResult(
            original_claim=claim.text,
            verdict=VerdictType.ERROR.value,
            confidence=0.0,
            evidence_summary=f"Error processing claim: {error_message}",
            sources=[],
            processing_time=processing_time,
            error_message=error_message
        )
