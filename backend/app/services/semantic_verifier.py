import re
import math
from typing import List, Optional
from app.config import settings
from app.utils.logger import logger


class SemanticVerifier:
    """
    Computes semantic similarity between claims and evidence text.
    Employs SentenceTransformers embeddings when available, with a fast
    sub-word cosine similarity fallback.
    """

    def __init__(self):
        self.model = None
        self._initialized = False

    def _lazy_init(self):
        if self._initialized:
            return
        self._initialized = True
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded SentenceTransformer model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.info(f"Using lightweight semantic tokenizer fallback: {e}")
            self.model = None

    def compute_similarity(self, claim: str, evidence: str) -> float:
        self._lazy_init()

        if self.model is not None:
            try:
                import numpy as np
                embeddings = self.model.encode([claim, evidence])
                v1, v2 = embeddings[0], embeddings[1]
                dot = np.dot(v1, v2)
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                cosine = float(dot / (norm1 * norm2))
                return max(0.0, min(1.0, (cosine + 1.0) / 2.0))
            except Exception as e:
                logger.warning(f"Error in embedding inference, falling back: {e}")

        return self._token_cosine_similarity(claim, evidence)

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
        # Generate word tokens + bi-grams for semantic context
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        return words + bigrams

    def _token_cosine_similarity(self, text1: str, text2: str) -> float:
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0

        freq1 = {}
        for t in tokens1:
            freq1[t] = freq1.get(t, 0) + 1

        freq2 = {}
        for t in tokens2:
            freq2[t] = freq2.get(t, 0) + 1

        # Calculate cosine similarity
        all_tokens = set(freq1.keys()).union(set(freq2.keys()))
        dot = sum(freq1.get(t, 0) * freq2.get(t, 0) for t in all_tokens)
        norm1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        raw_sim = dot / (norm1 * norm2)

        # Content word coverage of the claim by the evidence (filtering function words)
        stopwords = {"the", "is", "are", "has", "have", "was", "were", "of", "in", "and", "to", "a", "an", "at"}
        c_words = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text1.lower())) - stopwords
        e_words = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text2.lower())) - stopwords
        
        if not c_words:
            c_words = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text1.lower()))
            e_words = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text2.lower()))

        coverage = len(c_words.intersection(e_words)) / max(len(c_words), 1)

        # Composite semantic score
        blended = (0.40 * raw_sim) + (0.60 * coverage)
        return max(0.0, min(1.0, round(blended, 4)))


semantic_verifier = SemanticVerifier()
