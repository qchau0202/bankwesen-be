from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB Settings
    MONGODB_URL: str
    DATABASE_NAME: str = "tuition_db"
    
    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Key Settings
    API_KEY: str
    ENABLE_API_KEY: bool = True
    
    # Service Settings
    SERVICE_NAME: str = "Tuition Service"
    SERVICE_PORT: int = 8002
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
