from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any

from app.database.session import get_db
from app.models.verification import VerificationRequestRecord, ClaimRecord, EvidenceRecord

router = APIRouter(prefix="/api", tags=["History & Analytics"])


@router.get("/history")
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieves paginated verification history."""
    stmt = (
        select(VerificationRequestRecord)
        .order_by(VerificationRequestRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    total_count_res = await db.execute(select(func.count(VerificationRequestRecord.id)))
    total_count = total_count_res.scalar() or 0

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "request_id": r.id,
                "platform": r.platform,
                "overall_score": r.overall_score,
                "overall_status": r.overall_status,
                "claims_count": r.claims_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "preview": r.original_text[:120] + "..." if len(r.original_text) > 120 else r.original_text
            }
            for r in records
        ]
    }


@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Provides summary statistics for the web dashboard."""
    total_req_res = await db.execute(select(func.count(VerificationRequestRecord.id)))
    total_requests = total_req_res.scalar() or 0

    total_claims_res = await db.execute(select(func.count(ClaimRecord.id)))
    total_claims = total_claims_res.scalar() or 0

    # Count by status
    status_counts_res = await db.execute(
        select(ClaimRecord.status, func.count(ClaimRecord.id)).group_by(ClaimRecord.status)
    )
    status_counts = dict(status_counts_res.all())

    # Average confidence
    avg_conf_res = await db.execute(select(func.avg(ClaimRecord.confidence)))
    avg_confidence = avg_conf_res.scalar() or 0.0

    # Counts by platform
    plat_counts_res = await db.execute(
        select(VerificationRequestRecord.platform, func.count(VerificationRequestRecord.id))
        .group_by(VerificationRequestRecord.platform)
    )
    platform_counts = dict(plat_counts_res.all())

    return {
        "total_requests": total_requests,
        "total_claims": total_claims,
        "average_confidence": round(float(avg_confidence), 4),
        "status_breakdown": {
            "verified": status_counts.get("VERIFIED", 0),
            "partially_supported": status_counts.get("PARTIALLY_SUPPORTED", 0),
            "contradicted": status_counts.get("CONTRADICTED", 0) + status_counts.get("LIKELY_HALLUCINATED", 0),
            "conflicting_evidence": status_counts.get("CONFLICTING_EVIDENCE", 0),
            "insufficient_evidence": status_counts.get("INSUFFICIENT_EVIDENCE", 0),
            "not_fact_checkable": status_counts.get("NOT_FACT_CHECKABLE", 0) + status_counts.get("UNVERIFIABLE", 0),
            "hallucinated": status_counts.get("CONTRADICTED", 0) + status_counts.get("LIKELY_HALLUCINATED", 0),
        },
        "platforms": platform_counts
    }


@router.get("/sources/{claim_id}")
async def get_sources_by_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retrieves all evidence sources linked to a specific claim ID."""
    stmt = select(EvidenceRecord).where(EvidenceRecord.claim_id == claim_id)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "reliability_score": r.reliability_score,
            "domain": r.domain
        }
        for r in records
    ]
