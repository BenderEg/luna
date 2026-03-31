from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.app.models.payment import Currency, PaymentStatus


class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    currency: Currency
    description: Optional[str] = Field(None, max_length=255)
    meta: Optional[dict] = Field(..., default_factory=dict)
    webhook_url: Optional[str] = None


class PaymentCreate(PaymentBase):
    ...


class PaymentShort(PaymentBase):
    id: UUID
    status: PaymentStatus
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class PaymentDetail(PaymentShort):
    idempotency_key: str
    updated_at: Optional[datetime]