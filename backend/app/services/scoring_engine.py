from typing import List, Tuple
from app.config import settings
from app.api.schemas import (
    ClaimResult,
    VerificationStatus,
    NLILabel,
    ClaimType,
    EvidenceItem
)


class HybridScoringEngine:
    """
    Synthesizes multiple orthogonal signals into a calibrated verification score.
    Formula: Final Score = w_e * S_evidence + w_n * S_nli + w_s * S_source + w_r * S_rule
    """

    def __init__(self):
        self.w_evidence = settings.WEIGHT_EVIDENCE
        self.w_nli = settings.WEIGHT_NLI
        self.w_source = settings.WEIGHT_SOURCE
        self.w_rule = settings.WEIGHT_RULE
        self.th_verified = settings.THRESHOLD_VERIFIED
        self.th_partial = settings.THRESHOLD_PARTIAL

    def compute_claim_score(
        self,
        claim_id: str,
        claim_text: str,
        claim_type: ClaimType,
        is_verifiable: bool,
        evidence: List[EvidenceItem],
        semantic_score: float,
        nli_label: NLILabel,
        nli_score: float,
        rule_score: float,
        rule_explanation: str
    ) -> ClaimResult:
        # Check if the claim is subjective opinion or speculative prediction
        if not is_verifiable:
            return ClaimResult(
                claim_id=claim_id,
                claim=claim_text,
                type=claim_type,
                status=VerificationStatus.NOT_FACT_CHECKABLE,
                confidence=1.00,  # Confident that this is a subjective opinion
                semantic_score=semantic_score,
                nli=NLILabel.NEUTRAL,
                nli_score=0.50,
                source_reliability=0.0,
                rule_score=rule_score,
                evidence=[],
                explanation="Subjective statement or opinion; cannot be empirically verified as true or false."
            )

        # 1. Deterministic Rule Failure (Checks override probabilistic web search)
        if rule_score == 0.0:
            top_source_rel = max((e.reliability_score for e in evidence), default=0.5) if evidence else 0.5
            return ClaimResult(
                claim_id=claim_id,
                claim=claim_text,
                type=claim_type,
                status=VerificationStatus.CONTRADICTED,
                confidence=1.00,  # 100% confidence in deterministic contradiction
                semantic_score=round(semantic_score, 4),
                nli=NLILabel.CONTRADICTION,
                nli_score=1.00,
                source_reliability=round(top_source_rel, 4),
                rule_score=0.0,
                evidence=evidence,
                explanation=f"Deterministic rule contradiction: {rule_explanation}"
            )

        # 2. Handle zero external evidence: Critical rule - Must NEVER classify as hallucinated!
        if not evidence:
            return ClaimResult(
                claim_id=claim_id,
                claim=claim_text,
                type=claim_type,
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                semantic_score=0.0,
                nli=NLILabel.NEUTRAL,
                nli_score=0.0,
                source_reliability=0.0,
                rule_score=rule_score,
                evidence=[],
                explanation="No verifiable external sources could be retrieved to corroborate this claim."
            )

        # Top source reliability score
        top_source_rel = max((e.reliability_score for e in evidence), default=0.5)

        # 2. NLI Contradiction
        if nli_label == NLILabel.CONTRADICTION:
            return ClaimResult(
                claim_id=claim_id,
                claim=claim_text,
                type=claim_type,
                status=VerificationStatus.CONTRADICTED,
                confidence=round(max(0.75, nli_score), 4),  # High confidence in the contradiction status
                semantic_score=round(semantic_score, 4),
                nli=NLILabel.CONTRADICTION,
                nli_score=round(nli_score, 4),
                source_reliability=round(top_source_rel, 4),
                rule_score=round(rule_score, 4),
                evidence=evidence,
                explanation="Retrieved external evidence directly contradicts this claim."
            )

        # 3. Evidence Support Score
        evidence_support = (semantic_score * 0.6) + (top_source_rel * 0.4)
        nli_val = nli_score if nli_label == NLILabel.ENTAILMENT else 0.50

        # Composite verification score
        raw_score = (
            (self.w_evidence * evidence_support) +
            (self.w_nli * nli_val) +
            (self.w_source * top_source_rel) +
            (self.w_rule * rule_score)
        )
        final_support = round(max(0.0, min(1.0, raw_score)), 4)

        # Status categorization
        if final_support >= self.th_verified and nli_label == NLILabel.ENTAILMENT:
            status = VerificationStatus.VERIFIED
            confidence = final_support
            explanation = "Credible external evidence corroborates and entails this claim."
        elif final_support >= self.th_partial:
            status = VerificationStatus.PARTIALLY_SUPPORTED
            confidence = final_support
            explanation = "Available evidence partially supports this claim, but full corroboration is incomplete."
        else:
            status = VerificationStatus.INSUFFICIENT_EVIDENCE
            confidence = round(1.0 - final_support, 4)
            explanation = "Available external sources do not provide sufficient clear support for this claim."

        if top_source_rel >= 0.90 and status == VerificationStatus.VERIFIED:
            explanation += " Supported by high-reliability official or academic sources."

        return ClaimResult(
            claim_id=claim_id,
            claim=claim_text,
            type=claim_type,
            status=status,
            confidence=confidence,
            semantic_score=round(semantic_score, 4),
            nli=nli_label,
            nli_score=round(nli_score, 4),
            source_reliability=round(top_source_rel, 4),
            rule_score=round(rule_score, 4),
            evidence=evidence,
            explanation=explanation
        )

    def compute_overall_metrics(self, claim_results: List[ClaimResult]) -> Tuple[float, VerificationStatus, dict]:
        if not claim_results:
            return 0.0, VerificationStatus.INSUFFICIENT_EVIDENCE, {
                "total_claims": 0,
                "fact_checkable_claims": 0,
                "verified": 0,
                "partially_supported": 0,
                "contradicted": 0,
                "conflicting_evidence": 0,
                "insufficient_evidence": 0,
                "not_fact_checkable": 0,
                "hallucinated": 0
            }

        total_claims = len(claim_results)
        fact_checkable = [c for c in claim_results if c.status != VerificationStatus.NOT_FACT_CHECKABLE]

        counts = {
            "total_claims": total_claims,
            "fact_checkable_claims": len(fact_checkable),
            "verified": sum(1 for c in claim_results if c.status == VerificationStatus.VERIFIED),
            "partially_supported": sum(1 for c in claim_results if c.status == VerificationStatus.PARTIALLY_SUPPORTED),
            "contradicted": sum(1 for c in claim_results if c.status == VerificationStatus.CONTRADICTED),
            "conflicting_evidence": sum(1 for c in claim_results if c.status == VerificationStatus.CONFLICTING_EVIDENCE),
            "insufficient_evidence": sum(1 for c in claim_results if c.status == VerificationStatus.INSUFFICIENT_EVIDENCE),
            "not_fact_checkable": sum(1 for c in claim_results if c.status == VerificationStatus.NOT_FACT_CHECKABLE),
        }
        counts["hallucinated"] = counts["contradicted"]

        # Calculate Overall Reliability over evaluated fact-checkable claims
        evaluated_claims = [
            c for c in fact_checkable
            if c.status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED, VerificationStatus.CONTRADICTED, VerificationStatus.CONFLICTING_EVIDENCE)
        ]

        if evaluated_claims:
            overall_score = round(
                (counts["verified"] * 1.0 + counts["partially_supported"] * 0.5) / len(evaluated_claims),
                4
            )
        elif counts["insufficient_evidence"] > 0:
            overall_score = 0.0
        else:
            overall_score = 1.0  # Only opinions present

        # Overall Status
        if counts["contradicted"] > 0:
            if counts["contradicted"] == len(evaluated_claims):
                overall_status = VerificationStatus.CONTRADICTED
            else:
                overall_status = VerificationStatus.PARTIALLY_SUPPORTED
        elif overall_score >= self.th_verified and counts["verified"] > 0:
            overall_status = VerificationStatus.VERIFIED
        elif overall_score >= self.th_partial:
            overall_status = VerificationStatus.PARTIALLY_SUPPORTED
        elif counts["insufficient_evidence"] == len(fact_checkable):
            overall_status = VerificationStatus.INSUFFICIENT_EVIDENCE
        else:
            overall_status = VerificationStatus.CONTRADICTED

        return overall_score, overall_status, counts


scoring_engine = HybridScoringEngine()
