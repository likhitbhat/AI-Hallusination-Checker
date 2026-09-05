import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class VerificationRequestRecord(Base):
    __tablename__ = "verification_requests"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_text = Column(Text, nullable=False)
    platform = Column(String(32), default="generic")
    overall_score = Column(Float, nullable=False)
    overall_status = Column(String(32), nullable=False)
    claims_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    claims = relationship("ClaimRecord", back_populates="request", cascade="all, delete-orphan")


class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(64), ForeignKey("verification_requests.id"), nullable=False)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(32), default="factual")
    status = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    semantic_score = Column(Float, default=0.0)
    nli_label = Column(String(32), default="NEUTRAL")
    nli_score = Column(Float, default=0.0)
    source_reliability = Column(Float, default=0.0)
    rule_score = Column(Float, default=1.0)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    request = relationship("VerificationRequestRecord", back_populates="claims")
    evidence = relationship("EvidenceRecord", back_populates="claim", cascade="all, delete-orphan")


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), ForeignKey("claims.id"), nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(String(2048), nullable=False)
    snippet = Column(Text, nullable=False)
    reliability_score = Column(Float, default=0.5)
    domain = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    claim = relationship("ClaimRecord", back_populates="evidence")
