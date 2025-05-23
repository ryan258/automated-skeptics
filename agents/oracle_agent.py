# automated_skeptic_mvp/agents/oracle_agent.py
"""
Oracle Agent with ensemble methods and advanced evidence analysis
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from data.models import Claim, Source, Evidence, VerificationResult, VerdictType
from llm.manager import LLMManager
from llm.base import LLMMessage

class OracleAgent:
    """Evidence synthesis and verdict generation with ensemble analysis"""
    
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.agent_name = "oracle"
        
        # Initialize LLM manager
        self.llm_manager = LLMManager(settings)
        self.has_llm = len(self.llm_manager.get_available_providers()) > 0
        
        self.confidence_threshold = settings.getfloat('PROCESSING', 'confidence_threshold', 0.7)
        self.enable_ensemble = getattr(settings, 'get', lambda *args: 'false')('PHASE6', 'enable_ensemble_voting', 'false').lower() == 'true'
        
        if self.has_llm:
            self.logger.info("Oracle initialized with LLM-powered evidence analysis")
        else:
            self.logger.warning("Oracle using basic analysis - no LLM available")
    
    def process(self, claim: Claim) -> VerificationResult:
        """Synthesize evidence and generate final verdict"""
        start_time = datetime.now()
        
        try:
            sources = getattr(claim, 'sources', [])
            
            if not sources:
                return self._create_insufficient_evidence_result(claim, start_time)
            
            # Use ensemble or single-model analysis
            if self.enable_ensemble and self.has_llm and len(sources) > 1:
                evidence_list = self._ensemble_analyze_evidence(claim, sources)
            elif self.has_llm:
                evidence_list = self._llm_analyze_evidence(claim, sources)
            else:
                evidence_list = self._basic_analyze_evidence(claim, sources)
            
            # Generate verdict with confidence calibration
            verdict, confidence = self._generate_verdict(evidence_list, claim)
            
            # Create evidence summary
            evidence_summary = self._create_evidence_summary(evidence_list, verdict, claim)
            
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
    
    def _ensemble_analyze_evidence(self, claim: Claim, sources: List[Source]) -> List[Evidence]:
        """Use ensemble of multiple models to analyze evidence"""
        evidence_list = []
        
        for source in sources:
            try:
                # Get ensemble analysis for this source
                system_message = LLMMessage(
                    role="system",
                    content="""You are an expert fact-checker analyzing evidence. Determine if a source supports, contradicts, or is neutral regarding a claim.

Respond in this exact format:
ASSESSMENT: [SUPPORTS/CONTRADICTS/NEUTRAL]
CONFIDENCE: [0.0-1.0]
RELEVANT_TEXT: [exact quote from source]
REASONING: [brief explanation]

Be objective and factual."""
                )
                
                user_message = LLMMessage(
                    role="user",
                    content=f"""Claim: "{claim.text}"

Source: {source.title}
Content: {source.content[:1500]}...

Analyze if this source supports, contradicts, or is neutral regarding the claim."""
                )
                
                # Get ensemble response
                response = self.llm_manager.generate_ensemble(
                    messages=[system_message, user_message],
                    voting_method='weighted',
                    temperature=0.1,
                    max_tokens=400
                )
                
                # Parse response
                analysis = self._parse_llm_evidence_analysis(response.content)
                
                evidence = Evidence(
                    source=source,
                    supporting_text=analysis.get('relevant_text', ''),
                    supports_claim=analysis.get('supports', None),
                    confidence=analysis.get('confidence', 0.5),
                    extraction_method="ensemble_analysis",
                    metadata={
                        'ensemble_method': response.metadata.get('ensemble_method', 'weighted'),
                        'ensemble_size': response.metadata.get('ensemble_size', 1)
                    }
                )
                
                evidence_list.append(evidence)
                
            except Exception as e:
                self.logger.error(f"Ensemble analysis failed for source '{source.title}': {str(e)}")
                # Fallback to single model
                evidence = self._analyze_single_source(claim, source)
                evidence_list.append(evidence)
        
        return evidence_list
    
    def _llm_analyze_evidence(self, claim: Claim, sources: List[Source]) -> List[Evidence]:
        """Use LLM to analyze evidence from sources"""
        evidence_list = []
        
        for source in sources:
            try:
                evidence = self._analyze_single_source(claim, source)
                evidence_list.append(evidence)
                
            except Exception as e:
                self.logger.error(f"LLM analysis failed for source '{source.title}': {str(e)}")
                # Fallback to basic analysis
                evidence = self._basic_analyze_single_source(claim, source)
                evidence_list.append(evidence)
        
        return evidence_list
    
    def _analyze_single_source(self, claim: Claim, source: Source) -> Evidence:
        """Analyze single source with LLM"""
        
        system_message = LLMMessage(
            role="system",
            content="""You are an expert fact-checker analyzing evidence. Determine if a source supports, contradicts, or is neutral regarding a claim.

IMPORTANT: Be objective and factual. Avoid bias.

Respond in this exact format:
ASSESSMENT: [SUPPORTS/CONTRADICTS/NEUTRAL]
CONFIDENCE: [0.0-1.0]
RELEVANT_TEXT: [exact quote from source]
REASONING: [brief explanation]"""
        )
        
        user_message = LLMMessage(
            role="user",
            content=f"""Claim: "{claim.text}"

Source Title: {source.title}
Source Content: {source.content[:1500]}...

Analyze if this source supports, contradicts, or is neutral regarding the claim."""
        )
        
        # Use bias-aware generation
        response = self.llm_manager.generate(
            messages=[system_message, user_message],
            agent_name=self.agent_name,
            content_context=claim.text,
            temperature=0.1,
            max_tokens=400
        )
        
        # Parse response
        analysis = self._parse_llm_evidence_analysis(response.content)
        
        return Evidence(
            source=source,
            supporting_text=analysis.get('relevant_text', ''),
            supports_claim=analysis.get('supports', None),
            confidence=analysis.get('confidence', 0.5),
            extraction_method="llm_analysis",
            metadata={
                'llm_metadata': response.metadata
            }
        )
    
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
    
    def _generate_verdict(self, evidence_list: List[Evidence], claim: Claim) -> Tuple[VerdictType, float]:
        """Generate verdict with enhanced confidence calibration"""
        if not evidence_list:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        # Separate evidence by support type
        supporting_evidence = [e for e in evidence_list if e.supports_claim is True]
        contradicting_evidence = [e for e in evidence_list if e.supports_claim is False]
        neutral_evidence = [e for e in evidence_list if e.supports_claim is None]
        
        # Calculate weighted scores
        supporting_score = self._calculate_weighted_evidence_score(supporting_evidence)
        contradicting_score = self._calculate_weighted_evidence_score(contradicting_evidence)
        
        total_score = supporting_score + contradicting_score
        
        if total_score == 0:
            return VerdictType.INSUFFICIENT_EVIDENCE, 0.0
        
        support_ratio = supporting_score / total_score
        
        # Enhanced verdict logic
        confidence = self._calibrate_confidence(support_ratio, evidence_list)
        
        if support_ratio >= 0.7 and supporting_evidence:
            verdict = VerdictType.SUPPORTED
            confidence = min(confidence * 0.9, 0.95)
        elif support_ratio <= 0.3 and contradicting_evidence:
            verdict = VerdictType.CONTRADICTED
            confidence = min((1 - confidence) * 0.9, 0.95)
        else:
            verdict = VerdictType.INSUFFICIENT_EVIDENCE
            confidence = 0.5
        
        return verdict, confidence
    
    def _calculate_weighted_evidence_score(self, evidence_list: List[Evidence]) -> float:
        """Calculate weighted score for evidence list"""
        total_score = 0.0
        
        for evidence in evidence_list:
            # Base score from confidence and source credibility
            base_score = evidence.confidence * evidence.source.credibility_score
            
            # Boost for ensemble analysis
            if evidence.extraction_method == "ensemble_analysis":
                base_score *= 1.2
            
            total_score += base_score
        
        return total_score
    
    def _calibrate_confidence(self, support_ratio: float, evidence_list: List[Evidence]) -> float:
        """Calibrate confidence based on evidence quality"""
        
        # Base confidence from support ratio
        base_confidence = abs(support_ratio - 0.5) * 2
        
        # Quality adjustment
        avg_evidence_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
        quality_factor = avg_evidence_confidence
        
        # Source diversity factor
        unique_sources = len(set(e.source.url for e in evidence_list))
        diversity_factor = min(unique_sources / 3.0, 1.0)
        
        # Combine factors
        calibrated_confidence = (
            base_confidence * 0.5 +
            quality_factor * 0.3 +
            diversity_factor * 0.2
        )
        
        return min(calibrated_confidence, 0.95)
    
    def _create_evidence_summary(self, evidence_list: List[Evidence], verdict: VerdictType, claim: Claim) -> str:
        """Create comprehensive evidence summary"""
        if not evidence_list:
            return "No evidence found to evaluate this claim."
        
        supporting_count = len([e for e in evidence_list if e.supports_claim is True])
        contradicting_count = len([e for e in evidence_list if e.supports_claim is False])
        neutral_count = len([e for e in evidence_list if e.supports_claim is None])
        
        summary_parts = []
        
        # Verdict explanation
        analysis_method = "ensemble voting" if self.enable_ensemble else "LLM analysis"
        summary_parts.append(f"Using {analysis_method}, this claim is {verdict.value}.")
        
        # Evidence breakdown
        summary_parts.append(f"Analyzed {len(evidence_list)} sources: {supporting_count} supporting, {contradicting_count} contradicting, {neutral_count} neutral.")
        
        # Key evidence
        if supporting_count > 0:
            supporting_evidence = [e for e in evidence_list if e.supports_claim is True]
            best_supporting = max(supporting_evidence, key=lambda e: e.confidence * e.source.credibility_score)
            if best_supporting.supporting_text:
                summary_parts.append(f"Key supporting evidence: \"{best_supporting.supporting_text[:200]}...\"")
        
        if contradicting_count > 0:
            contradicting_evidence = [e for e in evidence_list if e.supports_claim is False]
            best_contradicting = max(contradicting_evidence, key=lambda e: e.confidence * e.source.credibility_score)
            if best_contradicting.supporting_text:
                summary_parts.append(f"Key contradicting evidence: \"{best_contradicting.supporting_text[:200]}...\"")
        
        return " ".join(summary_parts)
    
    def _extract_supporting_text_basic(self, claim: str, content: str) -> str:
        """Extract relevant text from source content - basic version"""
        if not content:
            return ""
        
        claim_words = set(claim.lower().split())
        sentences = content.split('.')
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = claim_words.intersection(sentence_words)
            
            if len(overlap) >= min(2, len(claim_words) * 0.3):
                relevant_sentences.append(sentence.strip())
        
        return '. '.join(relevant_sentences[:2])
    
    def _assess_support_basic(self, claim: str, content: str) -> bool:
        """Basic assessment if content supports the claim"""
        if not content:
            return False
        
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        claim_words = set(claim_lower.split())
        content_words = set(content_lower.split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Check for negation indicators
        negation_patterns = [
            r'\bnot\s+' + '|'.join(claim_words),
            r'\bno\s+' + '|'.join(claim_words),
            r'\bnever\s+' + '|'.join(claim_words),
            r'\bfalse\s+' + '|'.join(claim_words),
        ]
        
        import re
        has_contextual_negation = any(re.search(pattern, content_lower) for pattern in negation_patterns)
        
        return overlap_ratio > 0.4 and not has_contextual_negation
    
    def _calculate_evidence_confidence_basic(self, claim: str, content: str, credibility_score: float) -> float:
        """Calculate confidence in evidence - basic version"""
        if not content:
            return 0.0
        
        claim_words = set(claim.lower().split())
        content_words = set(content.lower().split())
        
        overlap = claim_words.intersection(content_words)
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        content_length_factor = min(len(content) / 500, 1.0)
        
        confidence = (overlap_ratio * 0.5) + (credibility_score * 0.3) + (content_length_factor * 0.2)
        
        return min(confidence, 1.0)
    
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