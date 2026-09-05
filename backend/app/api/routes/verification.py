from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.schemas import VerifyRequest, VerifyResponse, ClaimResult, EvidenceItem, NLILabel, ClaimType, VerificationStatus
from app.services.result_generator import result_generator
from app.database.session import get_db
from app.models.verification import VerificationRequestRecord, ClaimRecord, EvidenceRecord

router = APIRouter(prefix="/api", tags=["Verification"])


@router.post("/verify", response_model=VerifyResponse)
async def verify_response(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Main verification endpoint processing AI responses through the hybrid verification pipeline."""
    try:
        return await result_generator.verify_text(request, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification pipeline failed: {str(e)}")


@router.get("/verification/{request_id}", response_model=VerifyResponse)
async def get_verification_details(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves an existing verification run by its request ID."""
    stmt = (
        select(VerificationRequestRecord)
        .where(VerificationRequestRecord.id == request_id)
        .options(
            selectinload(VerificationRequestRecord.claims).selectinload(ClaimRecord.evidence)
        )
    )
    result = await db.execute(stmt)
    rec = result.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Verification request not found.")

    claim_results = []
    verified_cnt = 0
    partial_cnt = 0
    hallucinated_cnt = 0
    insufficient_cnt = 0

    for c in rec.claims:
        if c.status == VerificationStatus.VERIFIED.value:
            verified_cnt += 1
        elif c.status == VerificationStatus.PARTIALLY_SUPPORTED.value:
            partial_cnt += 1
        elif c.status == VerificationStatus.LIKELY_HALLUCINATED.value:
            hallucinated_cnt += 1
        else:
            insufficient_cnt += 1

        ev_items = [
            EvidenceItem(
                title=e.title,
                url=e.url,
                snippet=e.snippet,
                reliability_score=e.reliability_score,
                domain=e.domain
            )
            for e in c.evidence
        ]

        claim_results.append(ClaimResult(
            claim_id=c.id,
            claim=c.claim_text,
            type=ClaimType(c.claim_type) if c.claim_type in ClaimType._value2member_map_ else ClaimType.FACTUAL,
            status=VerificationStatus(c.status),
            confidence=c.confidence,
            semantic_score=c.semantic_score,
            nli=NLILabel(c.nli_label) if c.nli_label in NLILabel._value2member_map_ else NLILabel.NEUTRAL,
            nli_score=c.nli_score,
            source_reliability=c.source_reliability,
            rule_score=c.rule_score,
            evidence=ev_items,
            explanation=c.explanation or ""
        ))

    return VerifyResponse(
        request_id=rec.id,
        overall_score=rec.overall_score,
        overall_status=VerificationStatus(rec.overall_status),
        claims_analyzed=len(claim_results),
        verified=verified_cnt,
        partially_supported=partial_cnt,
        hallucinated=hallucinated_cnt,
        insufficient_evidence=insufficient_cnt,
        claims=claim_results
    )
