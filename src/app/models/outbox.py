from enum import StrEnum

from sqlalchemy import (
    String,
    Numeric,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.models.base import BaseModel


class EventType(StrEnum):
    PAYMENT_NEW = "payment_new"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"


class Outbox(BaseModel):
    __tablename__ = "outbox"

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"),
        nullable=False
    )
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, name="outbox_status_enum"),
        default=OutboxStatus.PENDING,
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )