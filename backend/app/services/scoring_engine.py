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
                status=VerificationStatus.UNVERIFIABLE,
                confidence=0.50,
                semantic_score=semantic_score,
                nli=NLILabel.NEUTRAL,
                nli_score=0.50,
                source_reliability=0.0,
                rule_score=rule_score,
                evidence=[],
                explanation="Subjective statement or future projection; cannot be empirically verified as true/false."
            )

        # Handle zero external evidence: Must NEVER classify as hallucinated!
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
                explanation="No verifiable external sources could be retrieved for this claim."
            )

        # Top source reliability score
        top_source_rel = max((e.reliability_score for e in evidence), default=0.5)

        # NLI normalized signal
        if nli_label == NLILabel.ENTAILMENT:
            nli_val = nli_score
        elif nli_label == NLILabel.CONTRADICTION:
            nli_val = 1.0 - nli_score
        else:
            nli_val = 0.50

        # Evidence support score combines semantic overlap with source credibility
        evidence_support = (semantic_score * 0.6) + (top_source_rel * 0.4)

        # Composite score calculation
        raw_score = (
            (self.w_evidence * evidence_support) +
            (self.w_nli * nli_val) +
            (self.w_source * top_source_rel) +
            (self.w_rule * rule_score)
        )
        final_confidence = round(max(0.0, min(1.0, raw_score)), 4)

        # Determine Status
        if rule_score == 0.0 or nli_label == NLILabel.CONTRADICTION:
            status = VerificationStatus.LIKELY_HALLUCINATED
        elif final_confidence >= self.th_verified:
            status = VerificationStatus.VERIFIED
        elif final_confidence >= self.th_partial:
            status = VerificationStatus.PARTIALLY_SUPPORTED
        else:
            status = VerificationStatus.LIKELY_HALLUCINATED

        # Build comprehensive rationale
        explanation_parts = []
        if nli_label == NLILabel.CONTRADICTION:
            explanation_parts.append("Retrieved external evidence directly contradicts this claim.")
        elif nli_label == NLILabel.ENTAILMENT:
            explanation_parts.append("Credible external evidence corroborates and entails this claim.")
        else:
            explanation_parts.append("Evidence neither conclusively proves nor disproves the statement.")

        if rule_score == 0.0:
            explanation_parts.append(f"Mathematical or chronological check failed: {rule_explanation}")
        elif rule_score == 1.0 and ("verified" in rule_explanation.lower() or "arithmetic" in rule_explanation.lower()):
            explanation_parts.append(rule_explanation)

        if top_source_rel >= 0.90:
            explanation_parts.append("Supported by high-reliability official or academic sources.")

        explanation = " ".join(explanation_parts)

        return ClaimResult(
            claim_id=claim_id,
            claim=claim_text,
            type=claim_type,
            status=status,
            confidence=final_confidence,
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
                "verified": 0, "partially_supported": 0, "hallucinated": 0, "insufficient_evidence": 0
            }

        counts = {
            "verified": sum(1 for c in claim_results if c.status == VerificationStatus.VERIFIED),
            "partially_supported": sum(1 for c in claim_results if c.status == VerificationStatus.PARTIALLY_SUPPORTED),
            "hallucinated": sum(1 for c in claim_results if c.status == VerificationStatus.LIKELY_HALLUCINATED),
            "insufficient_evidence": sum(1 for c in claim_results if c.status == VerificationStatus.INSUFFICIENT_EVIDENCE),
        }

        # Calculate weighted average reliability
        verifiable = [c for c in claim_results if c.status != VerificationStatus.UNVERIFIABLE]
        if not verifiable:
            return 0.50, VerificationStatus.PARTIALLY_SUPPORTED, counts

        avg_score = round(sum(c.confidence for c in verifiable) / len(verifiable), 4)

        if counts["hallucinated"] > 0 and (counts["hallucinated"] / len(verifiable)) >= 0.5:
            overall_status = VerificationStatus.LIKELY_HALLUCINATED
        elif avg_score >= self.th_verified:
            overall_status = VerificationStatus.VERIFIED
        elif avg_score >= self.th_partial:
            overall_status = VerificationStatus.PARTIALLY_SUPPORTED
        else:
            overall_status = VerificationStatus.LIKELY_HALLUCINATED

        return avg_score, overall_status, counts


scoring_engine = HybridScoringEngine()
