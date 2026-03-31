import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.rabbit import RabbitBroker

from src.app.api import router
from src.app.configs.settings import settings
from src.app.utils.logger import get_logger, setup_logging
from src.app.utils.publisher import send_payment_to_queue


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    broker = RabbitBroker(settings.RABBIT_URL)
    await broker.start()
    if settings.PUBLISHER_ENABLED:
        logger.info("Starting publisher for payments")
        try:
            settings.TASKS.append(asyncio.create_task(send_payment_to_queue(broker), name="publisher"))
        except asyncio.CancelledError:
            logger.error("Publisher cancelled")
    yield
    for i in settings.TASKS:
        i.cancel()
        logger.info(f"Task '{i.get_name()}' cancelled")
    await asyncio.gather(*settings.TASKS, return_exceptions=True)
    logger.info("All tasks cancelled")
    await broker.stop()
    logger.info("Broker closed")

    
app = FastAPI(
    title="Luna Payment API",
    version="0.1.0",
    debug=settings.is_debug,
    docs_url="/docs" if settings.SWAGGER_ENABLED else None,
    redoc_url="/redoc" if settings.SWAGGER_ENABLED else None,
    lifespan=lifespan,
)

app.include_router(router)
