from uuid import UUID

from sqlalchemy import select

from src.app.services.base import BaseService
from src.app.exceptions.http_exceptions import (
    NotFoundError,
)
from src.app.models.outbox import EventType, Outbox
from src.app.models.payment import Payment, PaymentStatus
from src.app.schemas.payment import (
    PaymentCreate,
    PaymentDetail,
)


class PaymentService(BaseService):

    MODEL = Payment
    SCHEMA = PaymentDetail

    async def create(
        self,
        dto: PaymentCreate,
        idempotency_key: str,
    ) -> PaymentDetail:
        await self._check_not_exist(self.MODEL, "idempotency_key", idempotency_key)
        new_obj: Payment = await self.add(dto, extras = {"idempotency_key": idempotency_key}, do_commit=False)
        await self.session.flush()
        self.session.add(
            Outbox(
                event_type=EventType.PAYMENT_NEW,
                payload={
                    "payment_id": str(new_obj.id),
                    "webhook_url": new_obj.webhook_url,
                }
            )
        )
        await self.session.commit()
        return self.SCHEMA.model_validate(new_obj)
    
    def is_payment_active(self, obj: Payment) -> bool:
        if obj.status == PaymentStatus.PENDING:
            return True
        return False

    async def get_by_id(self, payment_id: UUID) -> PaymentDetail:
        records = await self.session.execute(
            select(self.MODEL)
            .filter(self.MODEL.id == payment_id),
        )
        build_result = await self._build_result(records)
        if not build_result:
            raise NotFoundError(f"Оплата с {payment_id=} отсутствует в БД")
        return build_result[0]

    async def set_is_paid(self, payment_id: UUID) -> None:
        obj = await self.session.get_one(self.MODEL, payment_id)
        obj.status = PaymentStatus.SUCCEEDED
        await self.session.commit()