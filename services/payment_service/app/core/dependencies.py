from fastapi import Header, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.db.mongodb import get_database
from app.services.payment_service import PaymentService


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


async def get_payment_service_dependency(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> PaymentService:
    """
    Dependency to get payment service instance.
    
    Returns:
        PaymentService instance
    """
    return PaymentService(db)
