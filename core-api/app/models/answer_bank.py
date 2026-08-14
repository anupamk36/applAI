import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import UUIDPKMixin


class AnswerBankEntry(Base, UUIDPKMixin):
    """Spec §3.2/§4 `answer_bank`. `value` is plaintext for now — Phase 0
    already flagged this table for the Phase 3 field-level AES-256-GCM pass
    (§9.2); naming it `value` rather than spec's literal `value_encrypted`
    so the column name doesn't lie about its current state.

    Only the minimal slice needed to unblock hard filters (FR-401) is
    seeded here (see SEMANTIC_KEY_REGISTRY in app/services/answer_bank.py)
    — the full India Answer Bank (§3.2: UAN, notice period, declarations,
    etc.) is deferred to Phase 1.6 when Tier 4/5 field resolution needs it.
    """

    __tablename__ = "answer_bank"
    __table_args__ = (UniqueConstraint("user_id", "semantic_key"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    semantic_key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    policy: Mapped[str] = mapped_column(String, default="auto_fill")  # auto_fill | ask_me | never
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
