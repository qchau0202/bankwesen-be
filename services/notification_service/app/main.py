from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

from app.core.config import settings
from app.api import notification_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Notification Service for email notifications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notification_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/hello")
async def hello():
    return {"message": "Hello from Notification Service!"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_PASSWORD)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/call-tuition")
async def call_tuition():
    tuition_url = os.getenv("TUITION_SERVICE_URL", "http://tuition_service:8005")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{tuition_url}/hello", timeout=5.0)
            return {"notification_service": "called Tuition service", "tuition_response": response.json()}
        except Exception as e:
            return {"notification_service": "error", "error": str(e)}
