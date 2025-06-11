from typing import Annotated

from fastapi import Depends

from src.services.token_service import TokenService
from src.utils.unit_of_work import IUnitOfWork, UnitOfWork


def get_token_service(uow: Annotated[IUnitOfWork, Depends(UnitOfWork)]) -> TokenService:
    return TokenService(uow)
