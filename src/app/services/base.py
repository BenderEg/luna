from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from src.app.configs.database import Base
from src.app.exceptions.http_exceptions import (
    DuplicationError,
)
from src.app.utils.logger import get_logger


logger = get_logger(__name__)
ModelType = TypeVar("ModelType", bound=Any)


class BaseService:

    MODEL = Base
    SCHEMA = BaseModel
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        data: BaseModel,
        extras: dict = None,
        do_commit: bool = True,
    ) -> ModelType:
        """Добавляет запись в базу данных"""
        if not extras:
            extras = {}
        new_obj = self.MODEL(**data.model_dump(), **extras)
        self.session.add(new_obj)
        if do_commit:
            await self.session.commit()
        return new_obj
    
    async def _build_result(self, records, **kwargs) -> list[BaseModel]:
        return [self.SCHEMA.model_validate(i) for i in records.scalars().all()]

    async def _check_not_exist(
        self,
        model: ModelType,
        param_name: str,
        param_value: Any,
    ) -> None:
        """Проверка на создание дублей"""
        pk = self._get_pk()
        record = await self.session.execute(
            select(
                func.count(pk),
            ).where(
                getattr(model, param_name) == param_value,
            )
        )
        if record.scalar_one() > 0:
            msg = f"{model.__name__} with {param_name} = {param_value} already exists"
            logger.error(msg)
            raise DuplicationError(msg)
        
    def _get_pk(self):
        return getattr(self.MODEL, inspect(self.MODEL).primary_key[0].name)