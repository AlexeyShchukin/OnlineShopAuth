from typing import Annotated
from fastapi import Request

from fastapi import Depends

from src.exceptions.service_exceptions import MissingTokenException
from src.services.token_service import TokenService
from src.utils.unit_of_work import IUnitOfWork, UnitOfWork


def get_token_service(uow: Annotated[IUnitOfWork, Depends(UnitOfWork)]) -> TokenService:
    return TokenService(uow)


def get_refresh_token_from_cookie(request: Request) -> str:
    """
    Extracts the refresh token from the request cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        MissingTokenException()
    return refresh_token
