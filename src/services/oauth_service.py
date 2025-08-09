from typing import Any, Optional

from jose import jwt, exceptions
import aiohttp
from fastapi import HTTPException

from src.api.schemas.oauth import GoogleIdTokenPayload
from src.core.config import settings
from src.core import constants
from src.loggers.loggers import logger
from src.utils.unit_of_work import IUnitOfWork


class OAuthService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def generate_google_oauth_redirect_uri(self, state: str) -> str:
        params = {
            "client_id": settings.OAUTH_GOOGLE_CLIENT_ID,
            "redirect_uri": settings.OAUTH_GOOGLE_REDIRECT_URI,
            "scope": constants.GOOGLE_DRIVE_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{constants.GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    async def verify_google_id_token(
            self,
            session: aiohttp.ClientSession,
            id_token: str
    ) -> GoogleIdTokenPayload:
        try:
            unverified_header = jwt.get_unverified_header(id_token)
            algorithms = [unverified_header['alg']]

            payload = jwt.decode(
                token=id_token,
                key=constants.GOOGLE_JWKS_URI,
                algorithms=algorithms,
                options={
                    "verify_aud": True,
                    "aud": settings.OAUTH_GOOGLE_CLIENT_ID,
                    "verify_exp": True,
                },
                http_session=session
            )

            return GoogleIdTokenPayload(**payload)

        except exceptions.JOSEError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token or verification failed: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred during token verification: {e}"
            )

    async def handle_google_callback(
            self, code: str, session: aiohttp.ClientSession
    ) -> tuple[dict[str, Any], dict[str, Any], Optional[str]]:
        tokens = await self._exchange_code_for_tokens(code, session)
        access_token, refresh_token = self._extract_tokens(tokens)
        user_info = await self._fetch_user_info(access_token, session)

        files_data = {}
        if constants.GOOGLE_DRIVE_READONLY_SCOPE in constants.GOOGLE_DRIVE_SCOPES:
            files_data = await self._fetch_drive_files(access_token, session)

        return user_info, files_data, refresh_token

    async def get_new_access_token(self, refresh_token: str) -> str:
        """
        Refreshes the Google access token using a refresh token.
        """
        refresh_data = {
            "refresh_token": refresh_token,
            "client_id": settings.OAUTH_GOOGLE_CLIENT_ID,
            "client_secret": settings.OAUTH_GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    constants.GOOGLE_TOKEN_URL, data=refresh_data
            ) as response:
                response.raise_for_status()
                tokens = await response.json()
                return tokens["access_token"]

    @staticmethod
    async def _exchange_code_for_tokens(
            code: str, session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        token_data = {
            "code": code,
            "client_id": settings.OAUTH_GOOGLE_CLIENT_ID,
            "client_secret": settings.OAUTH_GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        try:
            async with session.post(constants.GOOGLE_TOKEN_URL, data=token_data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"Google token exchange failed: {e.status} {e.message}")
            raise HTTPException(status_code=502, detail="Failed to exchange code with Google")

    @staticmethod
    async def _fetch_user_info(
            access_token: str, session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        async with session.get(
                settings.OAUTH_GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
        ) as response:
            response.raise_for_status()
            return await response.json()

    @staticmethod
    async def _fetch_drive_files(
            access_token: str, session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        async with session.get(
                constants.GOOGLE_DRIVE_FILES_URL,
                headers={"Authorization": f"Bearer {access_token}"}
        ) as response:
            response.raise_for_status()
            return await response.json()

    @staticmethod
    def _extract_tokens(tokens: dict) -> tuple[str, str]:
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from Google.")
        return access_token, refresh_token
