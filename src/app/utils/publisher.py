import asyncio

from faststream.rabbit import RabbitBroker
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.configs.database import async_session
from src.app.configs.settings import settings
from src.app.utils.logger import get_logger
from src.app.models.outbox import (
    EventType,
    Outbox,
    OutboxStatus,
)


logger = get_logger(__name__)


async def send_payment_to_queue(broker: RabbitBroker):
    while True:
        try:
            async with async_session() as session:
                session: AsyncSession
                result = await session.execute(
                    select(Outbox)
                    .filter(
                        Outbox.status == OutboxStatus.PENDING,
                        Outbox.event_type == EventType.PAYMENT_NEW,
                    )
                    .with_for_update(skip_locked=True)
                    .order_by(Outbox.created_at)
                    .limit(100) # might be adjusted if needed
                )
                objs = result.scalars().all()
                sent_ids = []
                for obj in objs:
                    try:
                        await broker.publish(
                            message=obj.payload,
                            queue=settings.PAYMENTS_QUEUE,
                            headers={"event_id": str(obj.id)},
                        )
                        sent_ids.append(obj.id)
                    except Exception:
                        logger.exception(f"Failed to publish outbox obj {obj.id} to payment queue")
                        continue
                if sent_ids:
                    await session.execute(
                        update(Outbox)
                        .where(Outbox.id.in_(sent_ids))
                        .values(status=OutboxStatus.SENT)
                    )
                await session.commit()
                await asyncio.sleep(1) # might be adjusted if needed
        except asyncio.CancelledError:
            logger.info("Publisher task cancelled")
            raise
        except Exception as err:
            logger.exception(err)