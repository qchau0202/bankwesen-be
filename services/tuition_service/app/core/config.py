from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB Settings
    MONGODB_URL: str
    DATABASE_NAME: str
    
    # JWT Settings (MUST match auth service)
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # API Key Settings
    API_KEY: str
    ENABLE_API_KEY: bool
    
    # Service Settings
    SERVICE_NAME: str
    SERVICE_PORT: int
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
