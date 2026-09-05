import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Hybrid AI Hallucination Checker"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database: uses SQLite async by default for easy zero-config local run, or PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./hallucination_checker.db"
    )

    # Security
    JWT_SECRET: str = "dev-secret-key-change-in-production-12345678"
    CORS_ORIGINS: list[str] = ["*"]

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # openai, anthropic, or rule_based_fallback
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    # Search Provider Configuration
    SEARCH_PROVIDER: str = "duckduckgo"  # duckduckgo, tavily, serper, or mock
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_RESULTS_PER_CLAIM: int = 5
    SEARCH_CACHE_TTL_SECONDS: int = 86400

    # Embedding & Semantic Verification
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # NLI Model
    NLI_MODEL: str = "roberta-large-mnli"

    # Hybrid Scoring Weights (sum = 1.0)
    WEIGHT_EVIDENCE: float = 0.35
    WEIGHT_NLI: float = 0.30
    WEIGHT_SOURCE: float = 0.20
    WEIGHT_RULE: float = 0.15

    # Verification Decision Thresholds
    THRESHOLD_VERIFIED: float = 0.70
    THRESHOLD_PARTIAL: float = 0.45

    # Source Reliability Ratings
    RELIABILITY_GOVERNMENT: float = 1.00
    RELIABILITY_ACADEMIC: float = 0.95
    RELIABILITY_UNIVERSITY: float = 0.90
    RELIABILITY_MAJOR_ORG: float = 0.90
    RELIABILITY_ENCYCLOPEDIA: float = 0.80
    RELIABILITY_MAJOR_NEWS: float = 0.80
    RELIABILITY_GENERAL: float = 0.55
    RELIABILITY_UNKNOWN: float = 0.30

    # Limits
    MAX_CLAIMS_PER_REQUEST: int = 25
    REQUEST_TIMEOUT_SECONDS: int = 45


settings = Settings()
