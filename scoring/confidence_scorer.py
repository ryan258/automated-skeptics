# automated_skeptic_mvp/scoring/confidence_scorer.py
"""
Enhanced Confidence Scoring System
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import statistics

@dataclass
class ConfidenceComponents:
    """Components that contribute to overall confidence"""
    source_credibility: float
    evidence_strength: float
    consensus_score: float
    bias_adjustment: float
    provider_reliability: float
    response_coherence: float

@dataclass 
class EnsembleVote:
    """Single vote in ensemble decision"""
    provider_name: str
    verdict: str
    raw_confidence: float
    response_quality: float
    bias_score: float

class ConfidenceScorer:
    """Calculates final confidence scores from multiple components"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.component_weights = {
            'source_credibility': 0.25,
            'evidence_strength': 0.25, 
            'consensus_score': 0.20,
            'bias_adjustment': 0.15,
            'provider_reliability': 0.10,
            'response_coherence': 0.05
        }
    
    def calculate_final_confidence(
        self, 
        components: ConfidenceComponents,
        ensemble_votes: List[EnsembleVote] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate final confidence score with detailed breakdown"""
        
        # Base confidence from weighted components
        base_confidence = self._calculate_base_confidence(components)
        
        # Ensemble adjustment if available
        ensemble_adjustment = 0.0
        ensemble_info = {}
        
        if ensemble_votes:
            ensemble_confidence, ensemble_info = self._calculate_ensemble_confidence(ensemble_votes)
            ensemble_adjustment = (ensemble_confidence - base_confidence) * 0.3
        
        # Final confidence
        final_confidence = max(0.0, min(1.0, base_confidence + ensemble_adjustment))
        
        breakdown = {
            'base_confidence': base_confidence,
            'ensemble_adjustment': ensemble_adjustment,
            'final_confidence': final_confidence,
            'component_breakdown': self._breakdown_components(components),
            'ensemble_info': ensemble_info
        }
        
        return final_confidence, breakdown
    
    def _calculate_base_confidence(self, components: ConfidenceComponents) -> float:
        """Calculate base confidence from components"""
        
        weighted_sum = (
            components.source_credibility * self.component_weights['source_credibility'] +
            components.evidence_strength * self.component_weights['evidence_strength'] +
            components.consensus_score * self.component_weights['consensus_score'] +
            components.bias_adjustment * self.component_weights['bias_adjustment'] +
            components.provider_reliability * self.component_weights['provider_reliability'] +
            components.response_coherence * self.component_weights['response_coherence']
        )
        
        return max(0.0, min(1.0, weighted_sum))
    
    def _calculate_ensemble_confidence(self, votes: List[EnsembleVote]) -> Tuple[float, Dict[str, Any]]:
        """Calculate confidence from ensemble votes"""
        
        if not votes:
            return 0.5, {}
        
        # Separate votes by verdict
        supported_votes = [v for v in votes if v.verdict == 'SUPPORTED']
        contradicted_votes = [v for v in votes if v.verdict == 'CONTRADICTED'] 
        neutral_votes = [v for v in votes if v.verdict == 'NEUTRAL']
        
        # Calculate weighted scores
        supported_score = self._calculate_verdict_score(supported_votes)
        contradicted_score = self._calculate_verdict_score(contradicted_votes)
        neutral_score = self._calculate_verdict_score(neutral_votes)
        
        total_score = supported_score + contradicted_score + neutral_score
        
        if total_score == 0:
            return 0.5, {'reason': 'no_valid_votes'}
        
        # Determine winning verdict
        verdict_scores = {
            'SUPPORTED': supported_score,
            'CONTRADICTED': contradicted_score,
            'NEUTRAL': neutral_score
        }
        
        winning_verdict = max(verdict_scores, key=verdict_scores.get)
        winning_score = verdict_scores[winning_verdict]
        
        # Confidence based on margin and quality
        margin = winning_score / total_score
        vote_quality = self._calculate_vote_quality(votes)
        
        ensemble_confidence = (margin * 0.7) + (vote_quality * 0.3)
        
        ensemble_info = {
            'total_votes': len(votes),
            'winning_verdict': winning_verdict,
            'margin': margin,
            'vote_quality': vote_quality,
            'verdict_breakdown': {
                'supported': len(supported_votes),
                'contradicted': len(contradicted_votes),
                'neutral': len(neutral_votes)
            }
        }
        
        return ensemble_confidence, ensemble_info
    
    def _calculate_verdict_score(self, votes: List[EnsembleVote]) -> float:
        """Calculate weighted score for votes of same verdict"""
        
        if not votes:
            return 0.0
        
        total_score = 0.0
        for vote in votes:
            bias_penalty = max(0.0, 1.0 - vote.bias_score)
            quality_factor = vote.response_quality
            confidence_factor = vote.raw_confidence
            
            vote_weight = confidence_factor * quality_factor * bias_penalty
            total_score += vote_weight
        
        return total_score
    
    def _calculate_vote_quality(self, votes: List[EnsembleVote]) -> float:
        """Calculate overall quality of votes"""
        
        if not votes:
            return 0.0
        
        quality_scores = [v.response_quality for v in votes]
        avg_quality = statistics.mean(quality_scores)
        
        bias_scores = [v.bias_score for v in votes]
        avg_bias = statistics.mean(bias_scores)
        bias_penalty = max(0.0, 1.0 - avg_bias)
        
        # Provider diversity bonus
        providers = set(v.provider_name for v in votes)
        diversity_bonus = min(len(providers) / 3.0, 1.0)
        
        vote_quality = (avg_quality * 0.6) + (bias_penalty * 0.3) + (diversity_bonus * 0.1)
        
        return max(0.0, min(1.0, vote_quality))
    
    def _breakdown_components(self, components: ConfidenceComponents) -> Dict[str, float]:
        """Create detailed breakdown of component contributions"""
        
        return {
            'source_credibility': {
                'value': components.source_credibility,
                'weight': self.component_weights['source_credibility'],
                'contribution': components.source_credibility * self.component_weights['source_credibility']
            },
            'evidence_strength': {
                'value': components.evidence_strength,
                'weight': self.component_weights['evidence_strength'],
                'contribution': components.evidence_strength * self.component_weights['evidence_strength']
            },
            'consensus_score': {
                'value': components.consensus_score,
                'weight': self.component_weights['consensus_score'],
                'contribution': components.consensus_score * self.component_weights['consensus_score']
            },
            'bias_adjustment': {
                'value': components.bias_adjustment,
                'weight': self.component_weights['bias_adjustment'],
                'contribution': components.bias_adjustment * self.component_weights['bias_adjustment']
            },
            'provider_reliability': {
                'value': components.provider_reliability,
                'weight': self.component_weights['provider_reliability'],
                'contribution': components.provider_reliability * self.component_weights['provider_reliability']
            },
            'response_coherence': {
                'value': components.response_coherence,
                'weight': self.component_weights['response_coherence'],
                'contribution': components.response_coherence * self.component_weights['response_coherence']
            }
        }
    
    def calculate_source_credibility(self, sources: List[Any]) -> float:
        """Calculate credibility score from sources"""
        
        if not sources:
            return 0.0
        
        credibility_scores = []
        for source in sources:
            if hasattr(source, 'credibility_score'):
                credibility_scores.append(source.credibility_score)
            else:
                # Estimate based on source type
                if hasattr(source, 'source_type'):
                    if source.source_type == 'wikipedia':
                        credibility_scores.append(0.9)
                    elif source.source_type == 'news':
                        credibility_scores.append(0.7)
                    else:
                        credibility_scores.append(0.5)
                else:
                    credibility_scores.append(0.5)
        
        return statistics.mean(credibility_scores)
    
    def calculate_evidence_strength(self, evidence_list: List[Any]) -> float:
        """Calculate strength of evidence"""
        
        if not evidence_list:
            return 0.0
        
        strength_scores = []
        for evidence in evidence_list:
            strength = 0.5
            
            # Boost for supporting text
            if hasattr(evidence, 'supporting_text') and evidence.supporting_text:
                text_length = len(evidence.supporting_text)
                if text_length > 100:
                    strength += 0.2
                elif text_length > 50:
                    strength += 0.1
            
            # Boost for high confidence
            if hasattr(evidence, 'confidence'):
                strength += evidence.confidence * 0.3
            
            strength_scores.append(min(strength, 1.0))
        
        return statistics.mean(strength_scores)
    
    def calculate_consensus_score(self, evidence_list: List[Any]) -> float:
        """Calculate consensus across evidence sources"""
        
        if not evidence_list:
            return 0.0
        
        supporting = len([e for e in evidence_list if getattr(e, 'supports_claim', None) is True])
        contradicting = len([e for e in evidence_list if getattr(e, 'supports_claim', None) is False])
        neutral = len([e for e in evidence_list if getattr(e, 'supports_claim', None) is None])
        
        total = len(evidence_list)
        
        if total == 0:
            return 0.0
        
        max_agreement = max(supporting, contradicting, neutral)
        consensus_ratio = max_agreement / total
        
        # Bonus for multiple supporting sources
        if supporting >= 2 and contradicting == 0:
            consensus_ratio = min(consensus_ratio + 0.2, 1.0)
        
        return consensus_ratio
    
    def calculate_bias_adjustment(self, bias_scores: List[float]) -> float:
        """Calculate bias adjustment factor"""
        
        if not bias_scores:
            return 1.0
        
        avg_bias = statistics.mean(bias_scores)
        adjustment = max(0.1, 1.0 - avg_bias)
        
        return adjustment