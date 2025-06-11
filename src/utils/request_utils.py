from fastapi import Request


def get_client_ip(request: Request) -> str:
    return request.client.host


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "")
