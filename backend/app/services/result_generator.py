import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas import (
    VerifyRequest,
    VerifyResponse,
    ClaimResult,
    VerificationStatus
)
from app.services.claim_extractor import claim_extractor
from app.services.claim_classifier import claim_classifier
from app.services.rule_engine import rule_engine
from app.services.evidence_retriever import evidence_retriever
from app.services.semantic_verifier import semantic_verifier
from app.services.nli_verifier import nli_verifier
from app.services.scoring_engine import scoring_engine
from app.models.verification import (
    VerificationRequestRecord,
    ClaimRecord,
    EvidenceRecord
)
from app.utils.logger import logger


class ResultGenerator:
    """Orchestrates the full end-to-end multi-signal verification pipeline."""

    async def verify_text(
        self,
        request_data: VerifyRequest,
        db: Optional[AsyncSession] = None
    ) -> VerifyResponse:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        logger.info(f"Starting verification {request_id} for platform: {request_data.platform}")

        # 1. Claim Extraction
        extracted_claims = await claim_extractor.extract_claims(request_data.text)
        if not extracted_claims:
            return VerifyResponse(
                request_id=request_id,
                overall_score=0.0,
                overall_status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                claims_analyzed=0,
                verified=0,
                partially_supported=0,
                hallucinated=0,
                insufficient_evidence=0,
                claims=[]
            )

        # 2. Claim Classification
        classified_claims = claim_classifier.classify_batch(extracted_claims)

        # 3. Multi-Signal Verification for each claim
        claim_results: List[ClaimResult] = []

        for claim in classified_claims:
            # A. Rule consistency check
            rule_score, rule_explanation = rule_engine.evaluate_claim(claim.text)

            # If claim is non-verifiable (e.g. opinion), score directly
            if not claim.is_verifiable:
                claim_res = scoring_engine.compute_claim_score(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    claim_type=claim.type,
                    is_verifiable=False,
                    evidence=[],
                    semantic_score=0.0,
                    nli_label=None,
                    nli_score=0.0,
                    rule_score=rule_score,
                    rule_explanation=rule_explanation
                )
                claim_results.append(claim_res)
                continue

            # B. Evidence Retrieval
            evidence_items = await evidence_retriever.retrieve_evidence(claim.text)

            if not evidence_items:
                claim_res = scoring_engine.compute_claim_score(
                    claim_id=claim.id,
                    claim_text=claim.text,
                    claim_type=claim.type,
                    is_verifiable=True,
                    evidence=[],
                    semantic_score=0.0,
                    nli_label=None,
                    nli_score=0.0,
                    rule_score=rule_score,
                    rule_explanation=rule_explanation
                )
                claim_results.append(claim_res)
                continue

            # C. Semantic Similarity & NLI against candidate evidence
            best_semantic = 0.0
            best_nli_label = None
            best_nli_score = 0.0

            for ev in evidence_items:
                sim = semantic_verifier.compute_similarity(claim.text, ev.snippet)
                if sim > best_semantic:
                    best_semantic = sim

                label, nli_conf = nli_verifier.verify(claim.text, ev.snippet)
                # Prioritize contradiction or high entailment
                if best_nli_label is None or label.value == "CONTRADICTION" or nli_conf > best_nli_score:
                    best_nli_label = label
                    best_nli_score = nli_conf

            # D. Compute Hybrid Verification Score
            claim_res = scoring_engine.compute_claim_score(
                claim_id=claim.id,
                claim_text=claim.text,
                claim_type=claim.type,
                is_verifiable=True,
                evidence=evidence_items,
                semantic_score=best_semantic,
                nli_label=best_nli_label,
                nli_score=best_nli_score,
                rule_score=rule_score,
                rule_explanation=rule_explanation
            )
            claim_results.append(claim_res)

        # 4. Overall Reliability & Categorization
        overall_score, overall_status, counts = scoring_engine.compute_overall_metrics(claim_results)

        # 5. Persist to Database if session available
        if db is not None:
            try:
                req_rec = VerificationRequestRecord(
                    id=request_id,
                    original_text=request_data.text,
                    platform=request_data.platform or "generic",
                    overall_score=overall_score,
                    overall_status=overall_status.value,
                    claims_count=len(claim_results)
                )
                db.add(req_rec)

                for cr in claim_results:
                    c_rec = ClaimRecord(
                        id=f"{request_id}_{cr.claim_id}",
                        request_id=request_id,
                        claim_text=cr.claim,
                        claim_type=cr.type.value,
                        status=cr.status.value,
                        confidence=cr.confidence,
                        semantic_score=cr.semantic_score,
                        nli_label=cr.nli.value if cr.nli else "NEUTRAL",
                        nli_score=cr.nli_score,
                        source_reliability=cr.source_reliability,
                        rule_score=cr.rule_score,
                        explanation=cr.explanation
                    )
                    db.add(c_rec)

                    for ev in cr.evidence[:3]:
                        ev_rec = EvidenceRecord(
                            id=f"ev_{uuid.uuid4().hex[:12]}",
                            claim_id=c_rec.id,
                            title=ev.title[:500],
                            url=ev.url[:2000],
                            snippet=ev.snippet,
                            reliability_score=ev.reliability_score,
                            domain=ev.domain or ""
                        )
                        db.add(ev_rec)

                await db.commit()
            except Exception as e:
                logger.error(f"Error persisting verification result to database: {e}")
                await db.rollback()

        return VerifyResponse(
            request_id=request_id,
            overall_score=overall_score,
            overall_status=overall_status,
            claims_analyzed=len(claim_results),
            fact_checkable_claims=counts.get("fact_checkable_claims", len(claim_results)),
            verified=counts["verified"],
            partially_supported=counts["partially_supported"],
            contradicted=counts["contradicted"],
            conflicting_evidence=counts["conflicting_evidence"],
            insufficient_evidence=counts["insufficient_evidence"],
            not_fact_checkable=counts["not_fact_checkable"],
            hallucinated=counts["hallucinated"],
            claims=claim_results
        )


result_generator = ResultGenerator()
