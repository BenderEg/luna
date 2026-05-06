from uuid import UUID

from src.app.exceptions.http_exceptions import NotFoundError
from src.app.models.outbox import EventType
from src.app.models.payment import Payment, PaymentStatus
from src.app.repositories.unit_of_work import UnitOfWork
from src.app.schemas.payment import PaymentCreate, PaymentDetail


class PaymentService:

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(self, dto: PaymentCreate, idempotency_key: str) -> PaymentDetail:
        await self.uow.payments.check_idempotency_key_free(idempotency_key)
        new_payment = await self.uow.payments.create(dto, idempotency_key)
        await self.uow.flush()
        await self.uow.outbox.add_event(
            event_type=EventType.PAYMENT_NEW,
            payload={
                "payment_id": str(new_payment.id),
                "webhook_url": new_payment.webhook_url,
            },
        )
        return PaymentDetail.model_validate(new_payment)

    async def get_by_id(self, payment_id: UUID) -> PaymentDetail:
        payment = await self.uow.payments.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Оплата с {payment_id=} отсутствует в БД")
        return PaymentDetail.model_validate(payment)

    async def set_is_paid(self, payment_id: UUID) -> None:
        payment = await self.uow.payments.get_one_by_id_or_raise(payment_id)
        payment.status = PaymentStatus.SUCCEEDED

    def is_payment_active(self, obj: Payment) -> bool:
        return obj.status == PaymentStatus.PENDING
