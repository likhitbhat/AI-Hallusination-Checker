import re
import json
from typing import List
import httpx
from app.config import settings
from app.utils.logger import logger
from app.api.schemas import ExtractedClaim, ClaimType


class ClaimExtractor:
    """
    Splits generative AI responses into atomic factual statements.
    Supports LLM extraction with an offline deterministic NLP fallback.
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.provider = settings.LLM_PROVIDER

    async def extract_claims(self, text: str) -> List[ExtractedClaim]:
        if not text or not text.strip():
            return []

        # Attempt LLM extraction if API key is provided
        if self.api_key and self.provider == "openai":
            try:
                llm_claims = await self._extract_with_openai(text)
                if llm_claims:
                    return llm_claims
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to rule-based segmenter: {e}")

        # Deterministic rule-based atomic sentence segmenter
        return self._rule_based_extract(text)

    async def _extract_with_openai(self, text: str) -> List[ExtractedClaim]:
        prompt = (
            "You are a factual claim extraction system. Split the following AI response into independent, "
            "atomic factual claims. Do NOT group compound ideas. Return ONLY a valid JSON object with the format:\n"
            "{\"claims\": [{\"id\": \"claim_1\", \"text\": \"statement...\"}]}\n\n"
            f"Input Text:\n\"\"\"{text}\"\"\""
        )

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            claims = []
            for i, item in enumerate(parsed.get("claims", [])):
                claims.append(ExtractedClaim(
                    id=f"claim_{i+1}",
                    text=item["text"].strip()
                ))
            return claims

    def _rule_based_extract(self, text: str) -> List[ExtractedClaim]:
        """Splits sentences, cleans markdown bullet points, and decouples coordinate clauses."""
        # Clean markdown headers, bold, italics
        cleaned = re.sub(r"#{1,6}\s*", "", text)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)

        # Split into initial sentence candidates
        raw_lines = re.split(r"[\n\r]+", cleaned)
        candidates = []

        for line in raw_lines:
            line = line.strip()
            # Strip list prefixes: "1.", "1)", "-", "*", "•"
            line = re.sub(r"^(\d+[\.\)]|\-|\*|•)\s*", "", line)
            if not line:
                continue

            # Split by period, exclamation, question mark, or semicolons followed by whitespace
            sentences = re.split(r"(?<=[.!?])\s+|;\s*", line)
            for s in sentences:
                s = s.strip()
                if len(s) > 10:
                    candidates.append(s)

        atomic_claims = []
        counter = 1

        for sentence in candidates:
            # Check for coordinate clauses with numbers e.g.
            # "India has 28 states and 8 Union Territories" -> 2 claims
            coord_match = re.match(r"^(.+?)\s+(?:and|as well as)\s+([0-9]+\s+.+)$", sentence, re.IGNORECASE)
            if coord_match and len(sentence.split()) > 7:
                part1 = coord_match.group(1).strip()
                part2 = coord_match.group(2).strip()
                # If part2 lacks a subject, infer it from part1
                subject_match = re.match(r"^([A-Z][a-zA-Z\s]+?\b(?:has|have|contains|includes|is|was))\s+", part1)
                if subject_match and not re.match(r"^[A-Z][a-zA-Z\s]+?\b(?:has|have|is|was)", part2):
                    verb_phrase = subject_match.group(1)
                    part2_text = f"{verb_phrase} {part2}."
                else:
                    part2_text = f"{part2}."
                
                if not part1.endswith("."):
                    part1 += "."
                
                atomic_claims.append(ExtractedClaim(id=f"claim_{counter}", text=part1))
                counter += 1
                atomic_claims.append(ExtractedClaim(id=f"claim_{counter}", text=part2_text))
                counter += 1
            else:
                if not sentence.endswith((".", "!", "?")):
                    sentence += "."
                atomic_claims.append(ExtractedClaim(id=f"claim_{counter}", text=sentence))
                counter += 1

            if counter > settings.MAX_CLAIMS_PER_REQUEST:
                break

        return atomic_claims


claim_extractor = ClaimExtractor()
