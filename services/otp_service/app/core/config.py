from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Service Info
    SERVICE_NAME: str
    SERVICE_PORT: int
    
    # Redis Configuration
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_URL: str
    
    # OTP Configuration
    OTP_LENGTH: int
    OTP_EXPIRATION: int
    OTP_MAX_ATTEMPTS: int
    OTP_ATTEMPT_WINDOW: int
    
    # External Services
    NOTIFICATION_SERVICE_URL: str
    
    # API Key Configuration
    API_KEY: str
    API_KEY_NAME: str
    ENABLE_API_KEY: bool
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
