import asyncio

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.configs.database import async_session
from src.app.configs.settings import settings
from src.app.repositories.outbox import OutboxRepository
from src.app.utils.logger import get_logger


logger = get_logger(__name__)


async def send_payment_to_queue(broker: RabbitBroker):
    while True:
        try:
            async with async_session() as session:
                session: AsyncSession
                repo = OutboxRepository(session)
                objs = await repo.get_pending_payments(limit=100)
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
                    await repo.mark_as_sent(sent_ids)
                await session.commit()
                await asyncio.sleep(1) # might be adjusted if needed
        except asyncio.CancelledError:
            logger.info("Publisher task cancelled")
            raise
        except Exception as err:
            logger.exception(err)
