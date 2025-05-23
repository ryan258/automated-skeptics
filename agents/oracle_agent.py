# automated_skeptic_mvp/agents/oracle_agent.py
"""
Enhanced Oracle Agent with LLM-powered evidence analysis
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from data.models import Claim, Source, Evidence, VerificationResult, VerdictType
from llm.manager import LLMManager
from llm.base import LLMMessage

class OracleAgent:
    """Enhanced evidence synthesis and verdict generation agent with LLM analysis"""
    
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.agent_name = "oracle"
        
        # Initialize LLM manager for semantic analysis
        self.llm_manager = LLMManager(settings)
        self.has_llm = len(self.llm_manager.get_available_providers()) > 0
        
        self.confidence_threshold = settings.getfloat('PROCESSING', 'confidence_threshold', 0.7)
        
        if self.has_llm:
            self.logger.info("Oracle initialized with LLM-powered evidence analysis")
        else:
            self.logger.warning("Oracle using basic analysis - no LLM available")
    
    def process(self, claim: Claim) -> VerificationResult:
        """Synthesize evidence and generate final verdict with LLM analysis"""
        start_time = datetime.now()
        
        try:
            # Get sources from claim
            sources = getattr(claim, 'sources', [])
            
            if not sources:
                return self._create_insufficient_evidence_result(claim, start_time)
            
            # Analyze evidence from sources using LLM
            if self.has_llm:
                evidence_list = self._llm_analyze_evidence(claim, sources)
            else:
                evidence_list = self._basic_analyze_evidence(claim, sources)
            
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
    
    def _llm_analyze_evidence(self, claim: Claim, sources: List[Source]) -> List[Evidence]:
        """Use LLM to analyze evidence from sources"""
        evidence_list = []
        
        for source in sources:
            try:
                # Create analysis prompt
                system_message = LLMMessage(
                    role="system",
                    content="""You are an expert fact-checker analyzing evidence. Your task is to determine if a source supports, contradicts, or is neutral regarding a claim.

Analyze carefully:
1. Does the source content directly support the claim?
2. Does it contradict the claim?
3. Is it neutral/irrelevant?
4. Extract the most relevant text that supports your assessment.

Respond in this exact format:
ASSESSMENT: [SUPPORTS/CONTRADICTS/NEUTRAL]
CONFIDENCE: [0.0-1.0]
RELEVANT_TEXT: [exact quote from source that supports your assessment]
REASONING: [brief explanation of your assessment]"""
                )
                
                user_message = LLMMessage(
                    role="user",
                    content=f"""Claim: "{claim.text}"

Source Title: {source.title}
Source Content: {source.content[:1500]}...

Analyze if this source supports, contradicts, or is neutral regarding the claim."""
                )
                
                # Get LLM analysis
                response = self.llm_manager.generate(
                    messages=[system_message, user_message],
                    agent_name=self.agent_name,
                    temperature=0.1,
                    max_tokens=400
                )
                
                # Parse LLM response
                analysis = self._parse_llm_evidence_analysis(response.content)
                
                evidence = Evidence(
                    source=source,
                    supporting_text=analysis.get('relevant_text', ''),
                    supports_claim=analysis.get('supports', None),
                    confidence=analysis.get('confidence', 0.5),
                    extraction_method="llm_analysis"
                )
                
                evidence_list.append(evidence)
                
                self.logger.info(f"LLM evidence analysis for '{source.title}': {analysis.get('assessment', 'UNKNOWN')} (confidence: {analysis.get('confidence', 0):.2f})")
                
            except Exception as e:
                self.logger.error(f"LLM evidence analysis failed for source '{source.title}': {str(e)}")
                # Fallback to basic analysis
                evidence = self._basic_analyze_single_source(claim, source)
                evidence_list.append(evidence)
        
        return evidence_list
    
    def _parse_llm_evidence_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        analysis = {
            'assessment': 'NEUTRAL',
            'supports': None,
            'confidence': 0.5,
            'relevant_text': '',
            'reasoning': ''
        }
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('ASSESSMENT:'):
                assessment = line.split(':', 1)[1].strip().upper()
                analysis['assessment'] = assessment
                if assessment == 'SUPPORTS':
                    analysis['supports'] = True
                elif assessment == 'CONTRADICTS':
                    analysis['supports'] = False
                else:
                    analysis['supports'] = None
                    
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                    analysis['confidence'] = max(0.0, min(1.0, confidence))
                except:
                    pass
                    
            elif line.startswith('RELEVANT_TEXT:'):
                analysis['relevant_text'] = line.split(':', 1)[1].strip()
                
            elif line.startswith('REASONING:'):
                analysis['reasoning'] = line.split(':', 1)[1].strip()
        
        return analysis
    
    def _basic_analyze_evidence(self, claim: Claim, sources: List[Source]) -> List[Evidence]:
        """Fallback basic evidence analysis"""
        evidence_list = []
        
        for source in sources:
            evidence = self._basic_analyze_single_source(claim, source)
            evidence_list.append(evidence)
        
        return evidence_list
    
    def _basic_analyze_single_source(self, claim: Claim, source: Source) -> Evidence:
        """Basic analysis for a single source"""
        supporting_text = self._extract_supporting_text_basic(claim.text, source.content)
        supports_claim = self._assess_support_basic(claim.text, source.content)
        confidence = self._calculate_evidence_confidence_basic(claim.text, source.content, source.credibility_score)
        
        return Evidence(
            source=source,
            supporting_text=supporting_text,
            supports_claim=supports_claim,
            confidence=confidence,
            extraction_method="basic_analysis"
        )
    
    def _extract_supporting_text_basic(self, claim: str, content: str) -> str:
        """Extract relevant text from source content - basic version"""
        if not content:
            return ""
        
        # Find sentences containing claim keywords
        claim_words = set(claim.lower().split())
        sentences = content.split('.')
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = claim_words.intersection(sentence_words)
            
            # If sentence contains significant overlap with claim, include it
            if len(overlap) >= min(2, len(claim_words) * 0.3):
                relevant_sentences.append(sentence.strip())
        
        return '. '.join(relevant_sentences[:2])  # Limit to 2 sentences
    
    def _assess_support_basic(self, claim: str, content: str) -> bool:
        """Basic assessment if content supports the claim"""
        if not content:
            return False
        
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        # Look for exact matches or high overlap
        claim_words = set(claim_lower.split())
        content_words = set(content_lower.split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Check for negation indicators in context
        negation_patterns = [
            r'\bnot\s+' + '|'.join(claim_words),
            r'\bno\s+' + '|'.join(claim_words),
            r'\bnever\s+' + '|'.join(claim_words),
            r'\bfalse\s+' + '|'.join(claim_words),
        ]
        
        import re
        has_contextual_negation = any(re.search(pattern, content_lower) for pattern in negation_patterns)
        
        # Support if high overlap and no contextual negation
        return overlap_ratio > 0.4 and not has_contextual_negation
    
    def _calculate_evidence_confidence_basic(self, claim: str, content: str, credibility_score: float) -> float:
        """Calculate confidence in evidence - basic version"""
        if not content:
            return 0.0
        
        # Base confidence on keyword overlap and content length
        claim_words = set(claim.lower().split())
        content_words = set(content.lower().split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Boost for longer, more detailed content
        content_length_factor = min(len(content) / 500, 1.0)  # Normalize to 500 chars
        
        # Combine factors
        confidence = (overlap_ratio * 0.5) + (credibility_score * 0.3) + (content_length_factor * 0.2)
        
        return min(confidence, 1.0)
    
    def _generate_verdict(self, evidence_list: List[Evidence]) -> tuple[VerdictType, float]:
        """Generate verdict based on evidence analysis"""
        if not evidence_list:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        # Count supporting vs contradicting evidence
        supporting_evidence = [e for e in evidence_list if e.supports_claim is True]
        contradicting_evidence = [e for e in evidence_list if e.supports_claim is False]
        neutral_evidence = [e for e in evidence_list if e.supports_claim is None]
        
        # Calculate weighted scores
        supporting_score = sum(e.confidence * e.source.credibility_score for e in supporting_evidence)
        contradicting_score = sum(e.confidence * e.source.credibility_score for e in contradicting_evidence)
        
        total_score = supporting_score + contradicting_score
        
        if total_score == 0:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        support_ratio = supporting_score / total_score
        
        # Determine verdict based on ratio and evidence quality
        if support_ratio >= 0.7 and supporting_evidence:
            verdict = VerdictType.SUPPORTED
            confidence = min(support_ratio * 0.9, 0.95)  # Cap at 95%
        elif support_ratio <= 0.3 and contradicting_evidence:
            verdict = VerdictType.CONTRADICTED
            confidence = min((1 - support_ratio) * 0.9, 0.95)  # Cap at 95%
        else:
            verdict = VerdictType.INSUFFICIENT_EVIDENCE
            confidence = 0.5
        
        return verdict, confidence
    
    def _create_evidence_summary(self, evidence_list: List[Evidence], verdict: VerdictType) -> str:
        """Create human-readable evidence summary"""
        if not evidence_list:
            return "No evidence found to evaluate this claim."
        
        supporting_count = len([e for e in evidence_list if e.supports_claim is True])
        contradicting_count = len([e for e in evidence_list if e.supports_claim is False])
        neutral_count = len([e for e in evidence_list if e.supports_claim is None])
        
        summary_parts = []
        
        # Verdict explanation
        if verdict == VerdictType.SUPPORTED:
            summary_parts.append(f"This claim is SUPPORTED by the available evidence.")
        elif verdict == VerdictType.CONTRADICTED:
            summary_parts.append(f"This claim is CONTRADICTED by the available evidence.")
        else:
            summary_parts.append(f"There is INSUFFICIENT EVIDENCE to verify this claim.")
        
        # Evidence breakdown
        summary_parts.append(f"Found {len(evidence_list)} sources: {supporting_count} supporting, {contradicting_count} contradicting, {neutral_count} neutral.")
        
        # Key evidence
        if supporting_count > 0:
            supporting_evidence = [e for e in evidence_list if e.supports_claim is True]
            best_supporting = max(supporting_evidence, key=lambda e: e.confidence)
            if best_supporting.supporting_text:
                summary_parts.append(f"Key supporting evidence: {best_supporting.supporting_text[:200]}...")
        
        if contradicting_count > 0:
            contradicting_evidence = [e for e in evidence_list if e.supports_claim is False]
            best_contradicting = max(contradicting_evidence, key=lambda e: e.confidence)
            if best_contradicting.supporting_text:
                summary_parts.append(f"Key contradicting evidence: {best_contradicting.supporting_text[:200]}...")
        
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