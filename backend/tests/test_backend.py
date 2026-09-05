import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.claim_extractor import claim_extractor
from app.services.claim_classifier import claim_classifier
from app.services.rule_engine import rule_engine
from app.services.source_reliability import source_reliability_scorer
from app.services.nli_verifier import nli_verifier
from app.services.scoring_engine import scoring_engine
from app.api.schemas import ExtractedClaim, ClaimType, NLILabel, VerificationStatus, EvidenceItem


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_claim_extraction():
    text = "India has 28 states and 8 Union Territories. The capital of Karnataka is Bengaluru. Karnataka was formed in 1956."
    claims = await claim_extractor.extract_claims(text)
    assert len(claims) >= 3
    texts = [c.text for c in claims]
    assert any("28 states" in t for t in texts)
    assert any("Union Territories" in t for t in texts)
    assert any("Bengaluru" in t for t in texts)


def test_claim_classification():
    c1 = ExtractedClaim(id="1", text="India has 28 states.")
    c2 = ExtractedClaim(id="2", text="Karnataka was formed in 1956.")
    c3 = ExtractedClaim(id="3", text="The capital of Karnataka is Bengaluru.")
    c4 = ExtractedClaim(id="4", text="I think this is the most beautiful city.")
    c5 = ExtractedClaim(id="5", text="Water boils at 100 degrees celsius.")

    classified = claim_classifier.classify_batch([c1, c2, c3, c4, c5])
    assert classified[0].type == ClaimType.NUMERICAL
    assert classified[1].type == ClaimType.HISTORICAL
    assert classified[2].type == ClaimType.GEOGRAPHICAL
    assert classified[3].type == ClaimType.OPINION
    assert not classified[3].is_verifiable
    assert classified[4].type == ClaimType.SCIENTIFIC


def test_rule_engine():
    # True arithmetic
    s1, exp1 = rule_engine.evaluate_claim("25% of 200 is 50.")
    assert s1 == 1.0

    # False arithmetic
    s2, exp2 = rule_engine.evaluate_claim("25% of 200 is 60.")
    assert s2 == 0.0
    assert "contradicted" in exp2.lower()

    # Simple addition
    s3, _ = rule_engine.evaluate_claim("5 + 7 is 12.")
    assert s3 == 1.0

    # Future formed date
    s4, _ = rule_engine.evaluate_claim("Country was formed in 2099.")
    assert s4 == 0.0


def test_source_reliability():
    assert source_reliability_scorer.score_source("https://www.india.gov.in/portal") == 1.00
    assert source_reliability_scorer.score_source("https://oxford.edu/research") == 0.95
    assert source_reliability_scorer.score_source("https://en.wikipedia.org/wiki/India") == 0.80
    assert source_reliability_scorer.score_source("https://reuters.com/world") == 0.80
    assert source_reliability_scorer.score_source("https://random-unknown-blog.blogspot.com") == 0.30


def test_nli_verifier():
    # Entailment
    label1, _ = nli_verifier.verify(
        "Water boils at 100°C.",
        "At standard atmospheric pressure, water boils at 100°C."
    )
    assert label1 == NLILabel.ENTAILMENT

    # Contradiction due to number mismatch
    label2, _ = nli_verifier.verify(
        "India has 29 states.",
        "India comprises 28 states and 8 Union Territories."
    )
    assert label2 == NLILabel.CONTRADICTION


def test_scoring_insufficient_evidence():
    # Critical rule: lack of evidence must NOT be marked as hallucination!
    result = scoring_engine.compute_claim_score(
        claim_id="c_test",
        claim_text="Obscure unindexed factoid 12345.",
        claim_type=ClaimType.FACTUAL,
        is_verifiable=True,
        evidence=[],
        semantic_score=0.0,
        nli_label=NLILabel.NEUTRAL,
        nli_score=0.0,
        rule_score=1.0,
        rule_explanation=""
    )
    assert result.status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_full_verification_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "India has 28 states and 8 Union Territories. The capital of Australia is Sydney.",
            "platform": "chatgpt"
        }
        resp = await client.post("/api/verify", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "request_id" in data
        assert data["claims_analyzed"] >= 2
        assert len(data["claims"]) >= 2

        # Australia capital should be flagged as likely hallucinated or contradicted
        aus_claim = next((c for c in data["claims"] if "Australia" in c["claim"] or "Sydney" in c["claim"]), None)
        assert aus_claim is not None
        assert aus_claim["status"] in [VerificationStatus.CONTRADICTED.value, VerificationStatus.PARTIALLY_SUPPORTED.value]
