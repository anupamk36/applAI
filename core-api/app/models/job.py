import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.db import Base
from app.models.base import UUIDPKMixin


class Company(Base, UUIDPKMixin):
    __tablename__ = "companies"

    canonical_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    ats_detected: Mapped[str | None] = mapped_column(String, nullable=True)
    careers_url: Mapped[str | None] = mapped_column(String, nullable=True)
    size_band: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)


class Job(Base, UUIDPKMixin):
    __tablename__ = "jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    seniority_band: Mapped[str | None] = mapped_column(String, nullable=True)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    jd_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimensions), nullable=True
    )
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    exp_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    exp_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctc_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctc_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    locations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    countries: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    remote_policy: Mapped[str | None] = mapped_column(String, nullable=True)
    ats: Mapped[str | None] = mapped_column(String, nullable=True)
    apply_url: Mapped[str] = mapped_column(String, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ghost_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class JobSource(Base, UUIDPKMixin):
    __tablename__ = "job_sources"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_job_id: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
