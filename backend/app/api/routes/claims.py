from fastapi import APIRouter, HTTPException
from app.api.schemas import (
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    ClaimClassificationRequest,
    ClaimClassificationResponse,
    ExtractedClaim
)
from app.services.claim_extractor import claim_extractor
from app.services.claim_classifier import claim_classifier

router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("/extract", response_model=ClaimExtractionResponse)
async def extract_claims(payload: ClaimExtractionRequest):
    """Splits an AI-generated paragraph into atomic claims."""
    try:
        claims = await claim_extractor.extract_claims(payload.text)
        return ClaimExtractionResponse(claims=claims)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.post("/classify", response_model=ClaimClassificationResponse)
async def classify_claims(payload: ClaimClassificationRequest):
    """Classifies a list of claims into types (factual, numerical, opinion, etc.)."""
    try:
        extracted = [ExtractedClaim(id=f"c_{i+1}", text=t) for i, t in enumerate(payload.claims)]
        classified = claim_classifier.classify_batch(extracted)
        return ClaimClassificationResponse(classified_claims=classified)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim classification failed: {str(e)}")
