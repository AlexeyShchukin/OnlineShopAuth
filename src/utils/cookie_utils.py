from datetime import timedelta

from fastapi import Response


def set_refresh_token_in_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
        max_age=int(timedelta(days=7).total_seconds()),
    )


def delete_old_refresh_token_from_cookie(response: Response) -> None:
    response.delete_cookie("refresh_token", path="/")
