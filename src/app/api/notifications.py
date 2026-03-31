from http import HTTPStatus

from fastapi import APIRouter, Depends

from src.app.configs.di import (
    verify_api_key,
)
from src.app.utils.logger import get_logger

logger = get_logger(__name__)


router = APIRouter(
    prefix="/notifications",
    tags=["Уведомления"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    status_code=HTTPStatus.CREATED,
    description="Создание уведомления об оплате",
    summary="Создание уведомления об оплате",
)
async def create(
    notification_payload: dict,
) -> None:
    logger.info(f"Notification received: {notification_payload}")