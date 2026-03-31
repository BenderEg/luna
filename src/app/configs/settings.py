import asyncio
import yaml

from functools import cached_property
from typing import Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    BASE_API: str = "/api/v1"

    # Environment
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    ECHO: bool = False

    # Swagger/OpenAPI
    SWAGGER_ENABLED: bool = True
       
    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    CREDENTIALS_PATH: str = "./credentials.yaml"

    # RabbitMQ

    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBIT_HOST: str
    RABBIT_PORT: int = 5672
    PUBLISHER_ENABLED: bool = True
    PAYMENTS_QUEUE: str = "payments.new"
    NOTIFICATION_QUEUE: str = "notifications"
    PAYMENTS_RETRY_QUEUE: str = "payments_retry"
    PAYMENTS_DLQ: str = "payments_dlq"
    NOTIFICATION_DLQ: str = "notifications_dlq"
    MAX_RETRIES: int = 2

    TASKS: list[asyncio.Task] = []
    
    @property
    def is_debug(self) -> bool:
        return self.ENVIRONMENT == "dev"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @cached_property
    def API_KEY_LIST(self) -> set:
        with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            conf: dict[str, Any] = yaml.safe_load(f) or {}
            return set(conf.get("api_keys", []))
        
    @property
    def RABBIT_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_DEFAULT_USER}:{self.RABBITMQ_DEFAULT_PASS}@{self.RABBIT_HOST}:{self.RABBIT_PORT}/"


settings = Settings()