"""Security utilities for the Starluck Astro API."""

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.core.config import settings

class APIKeyAuth(HTTPBearer):
    """API Key authentication scheme. 
    It is Optional as this project aims a microservice architecure
    and accepts requests from the other machines in the network.
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


def verify_host(request: Request) -> None:
    """Verify that the request comes from an allowed host."""
    client_host = request.client.host
    
    if client_host not in settings.allowed_hosts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied from {client_host}"
        )


# Create auth dependency
api_key_auth = APIKeyAuth()
