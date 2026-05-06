from uuid import UUID

from sqlalchemy import select

from src.app.models.payment import Payment
from src.app.repositories.base import BaseRepository
from src.app.schemas.payment import PaymentCreate


class PaymentRepository(BaseRepository[Payment]):

    MODEL = Payment

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment).filter(Payment.id == payment_id)
        )
        return result.scalars().first()

    async def get_one_by_id_or_raise(self, payment_id: UUID) -> Payment:
        return await self.session.get_one(Payment, payment_id)

    async def create(self, dto: PaymentCreate, idempotency_key: str) -> Payment:
        instance = Payment(**dto.model_dump(), idempotency_key=idempotency_key)
        return await self.add(instance)

    async def check_idempotency_key_free(self, idempotency_key: str) -> None:
        await self.check_not_exist("idempotency_key", idempotency_key)
