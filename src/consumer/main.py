import asyncio
import json

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitMessage, RabbitQueue

from src.app.configs.settings import settings
from src.app.configs.database import async_session
from src.app.services.payment import PaymentService
from src.app.utils.logger import get_logger, setup_logging
from src.consumer.utils.aiohttp_session import (
    close_client_session,
    init_client_session,
)
from src.consumer.utils.exceptions import PaymentFailure
from src.consumer.utils.utils import (
    get_retry_delay_ms,
    mock_make_payment,
    mock_send_notification,
)


setup_logging()
logger = get_logger(__name__)

broker = RabbitBroker(settings.RABBIT_URL, log_level=2)
app = FastStream(broker)

payments_queue = RabbitQueue(
    settings.PAYMENTS_QUEUE,
    durable=True,
)
notification_queue = RabbitQueue(
    settings.NOTIFICATION_QUEUE,
    durable=True,
)

@app.on_startup
async def start_consumer():
    logger.info(f"Starting consumer")
    await broker.start()
    await broker.declare_queue(
        RabbitQueue(
            name=settings.PAYMENTS_RETRY_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": settings.PAYMENTS_QUEUE,
            },
        )
    )
    await broker.declare_queue(
        RabbitQueue(
            name=settings.PAYMENTS_DLQ,
            durable=True,
        )
    )
    await broker.declare_queue(
        RabbitQueue(
            name=settings.NOTIFICATION_DLQ,
            durable=True,
        )
    )
    await init_client_session()

@app.on_shutdown
async def stop_consumer():
    logger.info(f"Shutdown consumer")
    await broker.stop()
    await close_client_session()


@broker.subscriber(payments_queue)
async def handle_payment(msg: RabbitMessage):
    data = json.loads(msg.body)
    headers = msg.headers or {}
    retry_count = headers.get("x-retry-count", 0)
    async with async_session() as session:
        payment_service = PaymentService(session=session)
        try:
            await mock_make_payment(data, payment_service)
            logger.info(f"Succesfuly process payment msg from {settings.PAYMENTS_QUEUE} queue: {data}")
            await msg.ack()
            await broker.publish(
                data,
                queue=notification_queue,
                persist=True,
            )
        except PaymentFailure as err:
            logger.error(err)
            if retry_count >= settings.MAX_RETRIES:
                logger.info(f"Max retries exeeded. Sending message to DLQ: {data}")
                await broker.publish(
                    {
                        "error": str(err),
                        "error_type": "payment_fail",
                        "original_msg": data
                    },
                    queue=settings.PAYMENTS_DLQ,
                    headers=headers,
                    persist=True,
                )
                await msg.ack()
                return
            delay = get_retry_delay_ms(retry_count)
            logger.info(f"Sending message to retry queue with delay: {delay}")
            new_headers = dict(headers)
            new_headers["x-retry-count"] = retry_count + 1
            await broker.publish(
                data,
                queue=settings.PAYMENTS_RETRY_QUEUE,
                headers=new_headers,
                expiration=delay,
                persist=True,
            )
            await msg.ack()
        except Exception as err:
            await broker.publish(
                {
                    "error": str(err),
                    "error_type": "unhandled_payment_fail",
                    "original_msg": data
                },
                queue=settings.PAYMENTS_DLQ,
                headers=headers,
                persist=True,
            )
            await msg.ack()

@broker.subscriber(notification_queue)
async def handle_notification(msg: RabbitMessage):
    data = json.loads(msg.body)
    try:
        await mock_send_notification(data)
    except Exception as err:
        await broker.publish(
            {
                "error": str(err),
                "error_type": "notification_fail",
                "original_msg": data
            },
            queue=settings.NOTIFICATION_DLQ,
            persist=True,
        )
        await msg.ack()


if __name__ == "__main__":
    asyncio.run(app.run())