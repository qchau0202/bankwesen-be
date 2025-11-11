from fastapi import Header, HTTPException
from app.core.config import settings


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request header."""
    if not settings.ENABLE_API_KEY:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key is missing"
        )
    
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    
    return True
