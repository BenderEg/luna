from sqlalchemy.ext.asyncio import AsyncSession

from src.app.repositories.outbox import OutboxRepository
from src.app.repositories.payment import PaymentRepository


class UnitOfWork:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payments = PaymentRepository(session)
        self.outbox = OutboxRepository(session)

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, _exc_val, _exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        await self.session.commit()

    async def flush(self) -> None:
        await self.session.flush()

    async def rollback(self) -> None:
        await self.session.rollback()
