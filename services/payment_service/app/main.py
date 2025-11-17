from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.broker.redis_broker import connect_to_redis, close_redis_connection
from app.api.payment_routes import router as payment_router

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Payment Processing Service - Handles tuition payments with OTP verification",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(payment_router)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await connect_to_redis()
    print(f"{settings.SERVICE_NAME} started on port {settings.SERVICE_PORT}")
    print(f"API Key Security: {'ENABLED' if settings.ENABLE_API_KEY else 'DISABLED'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    await close_redis_connection()

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "database": settings.DATABASE_NAME,
        "api_key_enabled": settings.ENABLE_API_KEY
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment_service"}