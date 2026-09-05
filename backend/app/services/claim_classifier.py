import re
from typing import List
from app.api.schemas import ExtractedClaim, ClaimType


class ClaimClassifier:
    """Classifies atomic claims into taxonomy categories and determines verifiability."""

    OPINION_MARKERS = [
        r"\b(?:i think|in my opinion|best|worst|beautiful|ugly|amazing|terrible|awesome|superior|inferior|greatest)\b",
        r"\b(?:should|ought to|arguably|perhaps|maybe|probably)\b"
    ]
    PREDICTION_MARKERS = [
        r"\b(?:will likely|projected to|predicted to|in the future|by \d{4}|will soon|expected to)\b"
    ]
    NUMERICAL_MARKERS = [
        r"\b\d+(?:[\.,]\d+)?\b",
        r"\b(?:percent|%|million|billion|trillion|hundred|thousand)\b"
    ]
    HISTORICAL_MARKERS = [
        r"\b(?:in \d{3,4}|formed in|founded in|established in|during the war|century|ancient|discovered in|signed in|bc|ad)\b"
    ]
    GEOGRAPHICAL_MARKERS = [
        r"\b(?:capital of|located in|bordering|continent|ocean|river|mountain|lake|island|province|district|territory|city)\b"
    ]
    SCIENTIFIC_MARKERS = [
        r"\b(?:boils at|freezes at|gravity|atom|molecule|dna|rna|velocity|speed of light|celsius|fahrenheit|formula|photosynthesis)\b"
    ]
    DEFINITION_MARKERS = [
        r"\b(?:is defined as|refers to|is a term for|denotes|means)\b"
    ]

    def classify_claim(self, claim: ExtractedClaim) -> ExtractedClaim:
        text = claim.text.lower()

        # Check for opinions
        for pat in self.OPINION_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.OPINION
                claim.is_verifiable = False
                return claim

        # Check for future predictions
        for pat in self.PREDICTION_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.PREDICTION
                claim.is_verifiable = False
                return claim

        # Check historical
        for pat in self.HISTORICAL_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.HISTORICAL
                claim.is_verifiable = True
                return claim

        # Check scientific
        for pat in self.SCIENTIFIC_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.SCIENTIFIC
                claim.is_verifiable = True
                return claim

        # Check geographical
        for pat in self.GEOGRAPHICAL_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.GEOGRAPHICAL
                claim.is_verifiable = True
                return claim

        # Check definitions
        for pat in self.DEFINITION_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.DEFINITION
                claim.is_verifiable = True
                return claim

        # Check numerical / statistical
        if "%" in text or "percent" in text:
            claim.type = ClaimType.STATISTICAL
            claim.is_verifiable = True
            return claim

        for pat in self.NUMERICAL_MARKERS:
            if re.search(pat, text):
                claim.type = ClaimType.NUMERICAL
                claim.is_verifiable = True
                return claim

        # Default to general factual
        claim.type = ClaimType.FACTUAL
        claim.is_verifiable = True
        return claim

    def classify_batch(self, claims: List[ExtractedClaim]) -> List[ExtractedClaim]:
        return [self.classify_claim(c) for c in claims]


claim_classifier = ClaimClassifier()
