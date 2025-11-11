from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB Configuration (loaded from .env file)
    MONGODB_URL: str
    DATABASE_NAME: str = "auth_db"
    USERS_COLLECTION: str = "User"
    
    # JWT Configuration (loaded from .env file)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App Configuration
    APP_NAME: str = "Auth Service"
    DEBUG: bool = True
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"
    
    # API Key Configuration
    API_KEY: str = "your-api-key-change-in-production"
    API_KEY_NAME: str = "X-API-Key"
    ENABLE_API_KEY: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_origins(self) -> list:
        """Parse ALLOWED_ORIGINS string to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
