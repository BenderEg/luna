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


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(BaseModel):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_payment_idempotency_key",
        ),
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency_enum"),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True
    )
    webhook_url: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
