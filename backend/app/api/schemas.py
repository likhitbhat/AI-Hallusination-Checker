from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ClaimType(str, Enum):
    FACTUAL = "factual"
    NUMERICAL = "numerical"
    HISTORICAL = "historical"
    SCIENTIFIC = "scientific"
    GEOGRAPHICAL = "geographical"
    TEMPORAL = "temporal"
    STATISTICAL = "statistical"
    DEFINITION = "definition"
    CAUSAL = "causal"
    OPINION = "opinion"
    PREDICTION = "prediction"
    PROCEDURAL = "procedural"
    UNVERIFIABLE = "unverifiable"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_FACT_CHECKABLE = "NOT_FACT_CHECKABLE"


class NLILabel(str, Enum):
    ENTAILMENT = "ENTAILMENT"
    CONTRADICTION = "CONTRADICTION"
    NEUTRAL = "NEUTRAL"


# Models for Evidence
class EvidenceItem(BaseModel):
    title: str = Field(..., description="Source title or headline")
    url: str = Field(..., description="Canonical source URL")
    snippet: str = Field(..., description="Extracted contextual snippet")
    reliability_score: float = Field(0.5, description="Domain reliability rating")
    domain: Optional[str] = None


# Models for Claims
class ExtractedClaim(BaseModel):
    id: str
    text: str
    type: ClaimType = ClaimType.FACTUAL
    is_verifiable: bool = True


class ClaimResult(BaseModel):
    claim_id: str
    claim: str
    type: ClaimType
    status: VerificationStatus
    confidence: float
    semantic_score: float
    nli: NLILabel
    nli_score: float
    source_reliability: float
    rule_score: float
    evidence: List[EvidenceItem] = []
    explanation: str


# Verification API Payloads
class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=15000, description="AI-generated text response to verify")
    platform: Optional[str] = Field("generic", description="Source platform e.g. chatgpt, gemini, claude")


class VerifyResponse(BaseModel):
    request_id: str
    overall_score: float
    overall_status: VerificationStatus
    claims_analyzed: int
    fact_checkable_claims: int = 0
    verified: int = 0
    partially_supported: int = 0
    contradicted: int = 0
    conflicting_evidence: int = 0
    insufficient_evidence: int = 0
    not_fact_checkable: int = 0
    hallucinated: int = 0  # Compatibility field matching contradicted
    claims: List[ClaimResult]


class ClaimExtractionRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=15000)


class ClaimExtractionResponse(BaseModel):
    claims: List[ExtractedClaim]


class ClaimClassificationRequest(BaseModel):
    claims: List[str]


class ClaimClassificationResponse(BaseModel):
    classified_claims: List[ExtractedClaim]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
