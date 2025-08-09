from typing import Annotated

from fastapi import Depends

from src.services.oauth_service import OAuthService
from src.utils.unit_of_work import IUnitOfWork, UnitOfWork


def get_oauth_service(uow: Annotated[IUnitOfWork, Depends(UnitOfWork)]) -> OAuthService:
    return OAuthService(uow)
