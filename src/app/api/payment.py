from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends

from src.app.schemas.payment import (
    PaymentCreate,
    PaymentDetail,
    PaymentShort,
)
from src.app.configs.di import (
    get_payment_idempotency_key,
    payment_service,
    verify_api_key,
)


router = APIRouter(
    prefix="/payments",
    tags=["Оплата"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    status_code=HTTPStatus.ACCEPTED,
    description="Создание платежа в системе",
    summary="Создание платежа в системе",
    response_model=PaymentShort,
)
async def create(
    schema: PaymentCreate,
    service: payment_service,
    idempotency_key: str = Depends(get_payment_idempotency_key),
) -> PaymentShort:
    return await service.create(schema, idempotency_key)


@router.get(
    "/{payment_id}",
    status_code=HTTPStatus.OK,
    description="Получение шаблона по id",
    summary="Получение шаблона по id",
    response_model=PaymentDetail,
)
async def get_by_id(
    payment_id: UUID,
    service: payment_service,
) -> PaymentDetail:
    return await service.get_by_id(payment_id)
