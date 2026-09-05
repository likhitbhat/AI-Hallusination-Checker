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
    counts = {
        "verified": 0,
        "partially_supported": 0,
        "contradicted": 0,
        "conflicting_evidence": 0,
        "insufficient_evidence": 0,
        "not_fact_checkable": 0,
        "hallucinated": 0
    }

    for c in rec.claims:
        status_val = c.status
        if status_val == "LIKELY_HALLUCINATED":
            status_val = VerificationStatus.CONTRADICTED.value
        elif status_val == "UNVERIFIABLE":
            status_val = VerificationStatus.NOT_FACT_CHECKABLE.value

        status_enum = VerificationStatus(status_val) if status_val in VerificationStatus._value2member_map_ else VerificationStatus.INSUFFICIENT_EVIDENCE

        if status_enum == VerificationStatus.VERIFIED:
            counts["verified"] += 1
        elif status_enum == VerificationStatus.PARTIALLY_SUPPORTED:
            counts["partially_supported"] += 1
        elif status_enum == VerificationStatus.CONTRADICTED:
            counts["contradicted"] += 1
        elif status_enum == VerificationStatus.CONFLICTING_EVIDENCE:
            counts["conflicting_evidence"] += 1
        elif status_enum == VerificationStatus.NOT_FACT_CHECKABLE:
            counts["not_fact_checkable"] += 1
        else:
            counts["insufficient_evidence"] += 1

        counts["hallucinated"] = counts["contradicted"]

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
            status=status_enum,
            confidence=c.confidence,
            semantic_score=c.semantic_score,
            nli=NLILabel(c.nli_label) if c.nli_label in NLILabel._value2member_map_ else NLILabel.NEUTRAL,
            nli_score=c.nli_score,
            source_reliability=c.source_reliability,
            rule_score=c.rule_score,
            evidence=ev_items,
            explanation=c.explanation or ""
        ))

    overall_status_val = rec.overall_status
    if overall_status_val == "LIKELY_HALLUCINATED":
        overall_status_val = VerificationStatus.CONTRADICTED.value

    return VerifyResponse(
        request_id=rec.id,
        overall_score=rec.overall_score,
        overall_status=VerificationStatus(overall_status_val) if overall_status_val in VerificationStatus._value2member_map_ else VerificationStatus.INSUFFICIENT_EVIDENCE,
        claims_analyzed=len(claim_results),
        fact_checkable_claims=len(claim_results) - counts["not_fact_checkable"],
        verified=counts["verified"],
        partially_supported=counts["partially_supported"],
        contradicted=counts["contradicted"],
        conflicting_evidence=counts["conflicting_evidence"],
        insufficient_evidence=counts["insufficient_evidence"],
        not_fact_checkable=counts["not_fact_checkable"],
        hallucinated=counts["hallucinated"],
        claims=claim_results
    )
