from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from src.app.configs.database import Base
from src.app.exceptions.http_exceptions import DuplicationError
from src.app.utils.logger import get_logger


M = TypeVar("M", bound=Base) # type: ignore

logger = get_logger(__name__)


class BaseRepository(Generic[M]):

    MODEL: type[M]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _pk_column(self):
        return getattr(self.MODEL, inspect(self.MODEL).primary_key[0].name)

    async def add(self, instance: M) -> M:
        self.session.add(instance)
        return instance

    async def get_by_id(self, pk: UUID) -> M | None:
        return await self.session.get(self.MODEL, pk)

    async def check_not_exist(self, param_name: str, param_value: Any) -> None:
        pk = self._pk_column()
        result = await self.session.execute(
            select(func.count(pk)).where(
                getattr(self.MODEL, param_name) == param_value,
            )
        )
        if result.scalar_one() > 0:
            msg = f"{self.MODEL.__name__} with {param_name} = {param_value} already exists"
            logger.error(msg)
            raise DuplicationError(msg)
