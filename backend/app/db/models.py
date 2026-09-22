from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), nullable=False, default="analyst")
    created_at = Column(DateTime(timezone=True), nullable=True, default=_utcnow)

    cases = relationship("Case", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="open")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True, default=_utcnow)

    creator = relationship("User", back_populates="cases")
    alerts = relationship("Alert", back_populates="case")
    evidence = relationship("Evidence", back_populates="case")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")


class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author = Column(String(100), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True, default=_utcnow)

    case = relationship("Case", back_populates="notes")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    entity_id = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    anomaly_score = Column(Double, nullable=True)
    reason = Column(Text, nullable=False)
    evidence_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="new")
    created_at = Column(DateTime(timezone=True), nullable=True, default=_utcnow)

    case = relationship("Case", back_populates="alerts")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    source_type = Column(String(100), nullable=False)
    source_record_id = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    content_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    ingested_nodes = Column(JSON, nullable=True)
    ingested_edges = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True, default=_utcnow)

    case = relationship("Case", back_populates="evidence")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=True, default=_utcnow)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")
