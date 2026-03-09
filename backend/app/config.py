# backend/app/config.py
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List

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

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Monitoring
    MONITOR_CHECK_INTERVAL: int = 30  # seconds
    ALERT_COOLDOWN: int = 300  # 5 minutes

    # AI Agents
    ENABLE_AI_AGENTS: bool = True
    LLM_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_API_KEY: Optional[str] = None
    MAX_TOKENS: int = 1024

    # Alerts
    WEBHOOK_URL: str = ""

    @model_validator(mode="after")
    def check_secret_key_in_production(self) -> "Settings":
        if not self.DEBUG and self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be changed from the default value when running in production (DEBUG=False)"
            )
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
