"""Security utilities for the Starluck Astro API."""

from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import ipaddress

from app.core.config import settings


class APIKeyAuth(HTTPBearer):
    """
    API Key auth (optional). If settings.enable_api_key_auth is False,
    requests are allowed without a key.
    """
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        if not settings.enable_api_key_auth:
            return None

        credentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if credentials.credentials != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials


def _host_allowed(request: Request) -> bool:
    # If no restrictions configured, allow.
    if not settings.allowed_hosts:
        return True

    # Wildcard -> allow everything
    if "*" in settings.allowed_hosts:
        return True

    client_ip = (request.client.host if request.client else "") or ""
    host_hdr = (request.headers.get("host") or "").split(":")[0]

    # Exact string matches (IP or hostname)
    if client_ip in settings.allowed_hosts or host_hdr in settings.allowed_hosts:
        return True

    # CIDR support for entries like "172.19.0.0/16"
    try:
        ip = ipaddress.ip_address(client_ip)
        for entry in settings.allowed_hosts:
            if "/" in entry:
                try:
                    network = ipaddress.ip_network(entry, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    # skip malformed entries
                    pass
    except ValueError:
        # client_ip not a valid IP; ignore
        pass

    return False


def verify_host(request: Request) -> None:
    """Verify that the request comes from an allowed host/IP/CIDR."""
    if not _host_allowed(request):
        client_host = request.client.host if request.client else "unknown"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this host"
        )


# Expose auth dependency
api_key_auth = APIKeyAuth()
