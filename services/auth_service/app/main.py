from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db.mongodb import connect_to_mongodb, close_mongodb_connection
from .api.auth_routes import router as auth_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Authentication Service for Student Tuition Payment System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),  # Configure in .env file
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup."""
    await connect_to_mongodb()
    print("🚀 Auth Service started successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown."""
    await close_mongodb_connection()
    print("👋 Auth Service shutdown")


# Include routers
app.include_router(auth_router)


# Health check endpoints
@app.get("/")
async def root():
    return {
        "service": "Auth Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }
