from uuid import UUID

from sqlalchemy import select, update

from src.app.models.outbox import EventType, Outbox, OutboxStatus
from src.app.repositories.base import BaseRepository


class OutboxRepository(BaseRepository[Outbox]):

    MODEL = Outbox

    async def add_event(self, event_type: EventType, payload: dict) -> Outbox:
        instance = Outbox(event_type=event_type, payload=payload)
        return await self.add(instance)

    async def get_pending_payments(self, limit: int = 100) -> list[Outbox]:
        result = await self.session.execute(
            select(Outbox)
            .filter(
                Outbox.status == OutboxStatus.PENDING,
                Outbox.event_type == EventType.PAYMENT_NEW,
            )
            .with_for_update(skip_locked=True)
            .order_by(Outbox.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_as_sent(self, ids: list[UUID]) -> None:
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(status=OutboxStatus.SENT)
        )
