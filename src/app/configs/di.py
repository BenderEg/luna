from typing import Annotated

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.configs.database import get_session
from src.app.configs.settings import settings
from src.app.services.payment import PaymentService


def get_payment_service(
    session: AsyncSession = Depends(get_session),
) -> PaymentService:
    return PaymentService(session=session)


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key not in settings.API_KEY_LIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    
def get_payment_idempotency_key(idempotency_key: str = Header(..., alias="Idempotency-Key")) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Idempotency-Key must be provided",
        )
    return idempotency_key


payment_service = Annotated[PaymentService, Depends(get_payment_service)]