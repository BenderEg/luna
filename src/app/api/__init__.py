from fastapi import APIRouter

from src.app.configs.settings import settings
from src.app.api.notifications import router as notification_router
from src.app.api.payment import router as payment_router


router = APIRouter(prefix=settings.BASE_API)

router.include_router(payment_router)
router.include_router(notification_router)