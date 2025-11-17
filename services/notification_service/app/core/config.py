from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    # Service Info
    SERVICE_NAME: str
    SERVICE_PORT: int
    
    # Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str
    
    # External Services
    TUITION_SERVICE_URL: str
    
    # API Key Configuration
    API_KEY: str
    API_KEY_NAME: str
    ENABLE_API_KEY: bool
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
