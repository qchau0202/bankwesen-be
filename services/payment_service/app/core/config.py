from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB Settings
    MONGODB_URL: str
    DATABASE_NAME: str
    
    # JWT Settings (must match auth service)
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # API Key Settings
    API_KEY: str
    ENABLE_API_KEY: bool
    
    # Service Settings
    SERVICE_NAME: str
    SERVICE_PORT: int
    
    # External Service URLs
    AUTH_SERVICE_URL: str = "http://auth_service:8001"
    OTP_SERVICE_URL: str = "http://otp_service:8002"
    TUITION_SERVICE_URL: str = "http://tuition_service:8005"
    NOTIFICATION_SERVICE_URL: str = "http://notification_service:8004"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
