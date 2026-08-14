import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import UUIDPKMixin


class MatchScore(Base, UUIDPKMixin):
    __tablename__ = "match_scores"
    __table_args__ = (UniqueConstraint("user_id", "job_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    factors: Mapped[dict] = mapped_column(JSONB, nullable=False)
    hard_filter_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    threshold_at_time: Mapped[float] = mapped_column(Float, nullable=False)
