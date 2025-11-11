from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Payment Processing Service - Handles tuition payments",
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

# Startup event
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    print(f"🚀 {settings.SERVICE_NAME} started on port {settings.SERVICE_PORT}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "database": settings.DATABASE_NAME
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "payment_service"}
