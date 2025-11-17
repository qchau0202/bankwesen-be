from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str
    DATABASE_NAME: str
    USERS_COLLECTION: str
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # App Configuration
    APP_NAME: str
    DEBUG: bool
    
    # CORS Configuration
    ALLOWED_ORIGINS: str
    
    # API Key Configuration
    API_KEY: str
    API_KEY_NAME: str
    ENABLE_API_KEY: bool
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_origins(self) -> list:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
