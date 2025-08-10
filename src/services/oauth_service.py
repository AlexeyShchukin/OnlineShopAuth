import time
from typing import Any, Optional
from urllib.parse import urlencode

from jose import jwt, exceptions
import aiohttp
from fastapi import HTTPException, status

from src.api.schemas.oauth import GoogleIdTokenPayload
from src.core.config import settings
from src.core import constants
from src.loggers.loggers import logger
from src.utils.unit_of_work import IUnitOfWork


class OAuthService:

    def __init__(self, uow: IUnitOfWork):
        self.uow = uow
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0

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
        # return f"{constants.GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return f"{constants.GOOGLE_AUTH_URL}?{urlencode(params)}"

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
        try:
            tokens = await self._exchange_code_for_tokens(code, session)

            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            self.token_expiry = time.time() + tokens.get("expires_in", 3600)

            user_info = await self._fetch_user_info(session)
            files_data = {}
            if constants.GOOGLE_DRIVE_READONLY_SCOPE in constants.GOOGLE_DRIVE_SCOPES:
                files_data = await self._fetch_drive_files(session)

            return user_info, files_data, self.refresh_token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during Google callback handling: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during Google callback."
            )

    async def _refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
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
                return await response.json()

    async def _fetch_user_info(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        valid_access_token = await self._get_valid_access_token()
        async with session.get(
                settings.OAUTH_GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {valid_access_token}"}
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _fetch_drive_files(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        valid_access_token = await self._get_valid_access_token()
        async with session.get(
                constants.GOOGLE_DRIVE_FILES_URL,
                headers={"Authorization": f"Bearer {valid_access_token}"}
        ) as response:
            response.raise_for_status()
            return await response.json()

    # async def _fetch_drive_files(self, session: aiohttp.ClientSession) -> dict[str, Any]:
    #     valid_access_token = await self._get_valid_access_token()
    #     async with session.get(
    #             constants.GOOGLE_DRIVE_FILES_URL,
    #             headers={"Authorization": f"Bearer {valid_access_token}"}
    #     ) as response:
    #         text = await response.text()
    #         if response.status == 200:
    #             try:
    #                 return json.loads(text)
    #             except Exception:
    #                 logger.warning("Drive files response is not JSON, returning raw text")
    #                 return {"raw": text}
    #         elif response.status == 403:
    #             logger.error("Drive API returned 403 Forbidden: %s", text)
    #             raise HTTPException(status_code=403, detail=f"Google Drive API forbidden: {text}")
    #         else:
    #             logger.error("Drive API error: status=%s body=%s", response.status, text)
    #             raise HTTPException(status_code=502, detail="Failed to fetch drive files from Google")
    #
    # async def _fetch_user_info(self, session: aiohttp.ClientSession) -> dict[str, Any]:
    #     valid_access_token = await self._get_valid_access_token()
    #     async with session.get(
    #             settings.OAUTH_GOOGLE_USER_INFO_URL,
    #             headers={"Authorization": f"Bearer {valid_access_token}"}
    #     ) as response:
    #         text = await response.text()
    #         if response.status != 200:
    #             logger.error("Userinfo fetch failed: status=%s body=%s", response.status, text)
    #             raise HTTPException(status_code=502, detail="Failed to fetch user info from Google")
    #         return json.loads(text)

    async def _get_valid_access_token(self) -> str:
        """
        Returns a valid access token, refreshing it if it has expired.
        """
        if self.access_token and self.token_expiry > time.time():
            return self.access_token

        if not self.refresh_token:
            raise ValueError("Refresh token is missing. Cannot get new access token.")

        try:
            tokens = await self._refresh_access_token(self.refresh_token)
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token", self.refresh_token)
            self.token_expiry = time.time() + tokens.get("expires_in", 3600)
            return self.access_token
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise HTTPException(
                status_code=502,
                detail="Failed to refresh Google access token."
            )

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
        #         text = await response.text()
        #         if response.status != 200:
        #             logger.error(
        #                 "Google token exchange failed: status=%s, body=%s",
        #                 response.status, text
        #             )
        #             # CHANGED: пробрасываем понятную ошибку с телом от Google (без секрета)
        #             raise HTTPException(status_code=502, detail=f"Failed to exchange code with Google: {text}")
        #         tokens = json.loads(text)
        #         logger.info("Google token exchange successful; scopes: %s", tokens.get("scope"))
        #         return tokens
        # except aiohttp.ClientResponseError as e:
        #     # CHANGED: добавлено логирование статуса и текста (если доступно)
        #     logger.exception("ClientResponseError during token exchange: %s", e)
        #     raise HTTPException(status_code=502, detail="Failed to exchange code with Google")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"Google token exchange failed: {e.status} {e.message}")
            raise HTTPException(status_code=502, detail="Failed to exchange code with Google")
