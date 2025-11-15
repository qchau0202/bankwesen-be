from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
from ..core.security import decode_access_token
from ..schemas.auth import TokenData
from ..core.config import settings

# HTTP Bearer token security
security = HTTPBearer()

# API Key security
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Dependency to verify API key.
    
    Args:
        api_key: API key from request header
        
    Returns:
        The valid API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Skip API key check if disabled
    if not settings.ENABLE_API_KEY:
        return "disabled"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing API Key. Please provide '{settings.API_KEY_NAME}' header.",
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    
    return api_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials with Bearer token
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information
    username: str = payload.get("username")
    userid: str = payload.get("userid")
    
    if username is None or userid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(userid=userid, username=username)
