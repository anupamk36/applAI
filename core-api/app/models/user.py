import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin

DEFAULT_JOB_PREFERENCES = {
    "target_titles": [],
    "locations": [],
    "target_countries": ["IN"],
    "ctc_min": None,
    "ctc_max": None,
    "industries": [],
    "company_size_bands": [],
    "blocklist_companies": [],
}


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    plan: Mapped[str] = mapped_column(String, default="free")
    status: Mapped[str] = mapped_column(String, default="active")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    threshold: Mapped[float] = mapped_column(default=0.75)
    daily_cap: Mapped[int] = mapped_column(Integer, default=10)
    sensitive_field_policy: Mapped[dict] = mapped_column(JSONB, default=dict)
    job_preferences: Mapped[dict] = mapped_column(
        JSONB, default=lambda: dict(DEFAULT_JOB_PREFERENCES)
    )
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    calibration_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    calibration_count: Mapped[int] = mapped_column(Integer, default=0)
