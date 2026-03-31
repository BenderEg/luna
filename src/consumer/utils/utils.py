import asyncio
import random

from http import HTTPStatus
from uuid import UUID

import backoff

from src.app.configs.settings import settings
from src.app.services.payment import PaymentService
from src.consumer.utils.aiohttp_session import get_aiohttp_session
from src.consumer.utils.exceptions import (
    NotificationFailure,
    PaymentFailure,
)


def get_retry_delay_ms(retry_count: int) -> int:
    base = 1
    return base * (2 ** retry_count)


async def mock_make_payment(data: dict, payment_serice: PaymentService) -> None:
    payment_id = UUID(data.get("payment_id"))
    payment = await payment_serice.get_by_id(payment_id)
    if payment_serice.is_payment_active(payment):
        await payment_serice.session.commit() # to avoid holding transaction
        await asyncio.sleep(random.randint(2, 5))
        if random.random() >= 0.9:
            raise PaymentFailure(f"Failed to make payment for payload: {data}")
        else:
            await payment_serice.set_is_paid(payment_id)


@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=(NotificationFailure, asyncio.TimeoutError),
    max_tries=3,
)
async def mock_send_notification(data: dict) -> None:
    if random.random() >= 0.9:
        raise NotificationFailure(f"Failed to send notification for payload: {data}")
    else:
        client = await get_aiohttp_session()
        API_KEY = next(iter(settings.API_KEY_LIST))
        if not API_KEY:
            raise NotificationFailure(f"No valid API_KEY in settings")
        webhook_url = data.get("webhook_url")
        if not webhook_url:
            raise NotificationFailure(f"Webhook url was not provided in payment msg")
        async with client.post(
            url=webhook_url,
            headers={
                "X-API-Key": API_KEY,
            },
            json=data,
        ) as resp:
            if resp.status != HTTPStatus.CREATED:
                raise NotificationFailure(f"Failed to send notification. Http error with status code: {resp.status}")