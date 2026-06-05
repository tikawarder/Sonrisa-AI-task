import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    keywords: Mapped[list] = mapped_column(ARRAY(Text), nullable=False, default=list)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="alerts")  # noqa: F821
    matched_events: Mapped[list["MatchedEvent"]] = relationship(  # noqa: F821
        "MatchedEvent", back_populates="alert", cascade="all, delete-orphan"
    )
