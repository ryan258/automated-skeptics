# automated_skeptic_mvp/data/models.py
"""
Core data models for the Automated Skeptic MVP
FIXED: Added missing metadata field to Evidence class
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class ClaimType(Enum):
    """Types of claims the system can process"""
    HISTORICAL_DATE = "historical_date"
    BIOGRAPHICAL_FACT = "biographical_fact"
    CORPORATE_FACT = "corporate_fact"
    NEWS_EVENT = "news_event"
    UNKNOWN = "unknown"

class VerdictType(Enum):
    """Possible verification verdicts"""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ERROR = "ERROR"

@dataclass
class Entity:
    """Represents an extracted entity from a claim"""
    text: str
    entity_type: str  # PERSON, ORG, DATE, GPE, etc.
    start_pos: int
    end_pos: int
    confidence: float = 1.0

@dataclass
class SubClaim:
    """Represents a deconstructed sub-component of a claim"""
    text: str
    entities: List[Entity] = field(default_factory=list)
    claim_type: ClaimType = ClaimType.UNKNOWN
    verifiable: bool = True

@dataclass
class Source:
    """Represents a source of information"""
    url: str
    title: str
    content: str = ""
    source_type: str = "web"  # wikipedia, news, fact_check, web
    credibility_score: float = 0.5
    relevance_score: float = 0.0
    publication_date: Optional[datetime] = None

@dataclass
class Evidence:
    """Represents evidence for or against a claim"""
    source: Source
    supporting_text: str
    supports_claim: bool
    confidence: float
    extraction_method: str = "manual"
    metadata: Optional[Dict[str, Any]] = None  # FIXED: Added missing metadata field

@dataclass
class Claim:
    """Represents a claim to be verified"""
    text: str
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    claim_type: ClaimType = ClaimType.UNKNOWN
    entities: List[Entity] = field(default_factory=list)
    sub_claims: List[SubClaim] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class VerificationResult:
    """Represents the final verification result"""
    original_claim: str
    verdict: str
    confidence: float
    evidence_summary: str
    sources: List[Source] = field(default_factory=list)
    sub_claim_results: List[Dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None