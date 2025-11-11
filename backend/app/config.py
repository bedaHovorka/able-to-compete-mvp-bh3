# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AbleToCompete MVP"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/abletocompete"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Monitoring
    MONITOR_CHECK_INTERVAL: int = 30  # seconds
    ALERT_COOLDOWN: int = 300  # 5 minutes
    
    # AI Agents
    ENABLE_AI_AGENTS: bool = True
    LLM_MODEL: str = "gpt-4"  # or local model
    
    class Config:
        env_file = ".env"

settings = Settings()
