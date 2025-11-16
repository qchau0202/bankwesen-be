from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.redis import redis_client
from app.api import otp_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting OTP Service...")
    try:
        await redis_client.connect(settings.REDIS_URL)
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down OTP Service...")
    await redis_client.disconnect()
    logger.info("Disconnected from Redis")

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="OTP Service for payment verification",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(otp_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_healthy = await redis_client.redis.ping() if redis_client.redis else False
        
        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "redis": "connected" if redis_healthy else "disconnected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e)
        }

@app.get("/call-notification")
async def call_notification():
    notification_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8004")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{notification_url}/hello", timeout=5.0)
            return {"otp_service": "called Notification service", "notification_response": response.json()}
        except Exception as e:
            return {"otp_service": "error", "error": str(e)}
