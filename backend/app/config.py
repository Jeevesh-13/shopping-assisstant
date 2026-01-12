from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Application
    APP_NAME: str = "Shopping Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="CORS_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./shopping_agent.db",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=5, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Cache
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    
    # LLM Configuration - Google Gemini (Primary)
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    GEMINI_TEMPERATURE: float = Field(default=0.7, env="GEMINI_TEMPERATURE")
    GEMINI_MAX_TOKENS: int = Field(default=2048, env="GEMINI_MAX_TOKENS")
    
    # LLM Configuration - OpenAI (Fallback)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(default=2048, env="OPENAI_MAX_TOKENS")
    
    # LLM Configuration - Anthropic (Secondary Fallback)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # LLM Retry Configuration
    LLM_MAX_RETRIES: int = Field(default=3, env="LLM_MAX_RETRIES")
    LLM_RETRY_DELAY: int = Field(default=1, env="LLM_RETRY_DELAY")
    LLM_TIMEOUT: int = Field(default=30, env="LLM_TIMEOUT")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Observability
    ENABLE_METRICS: bool = Field(default=False, env="ENABLE_METRICS")
    ENABLE_TRACING: bool = Field(default=False, env="ENABLE_TRACING")
    
    # AIOps
    ENABLE_ANOMALY_DETECTION: bool = Field(default=True, env="ENABLE_ANOMALY_DETECTION")
    ANOMALY_THRESHOLD: float = Field(default=2.5, env="ANOMALY_THRESHOLD")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Safety & Content Moderation
    ENABLE_SAFETY_CHECKS: bool = Field(default=True, env="ENABLE_SAFETY_CHECKS")
    MAX_QUERY_LENGTH: int = Field(default=500, env="MAX_QUERY_LENGTH")
    BLOCKED_KEYWORDS: List[str] = Field(
        default=[
            "system prompt", "ignore instructions", "api key",
            "reveal", "hack", "jailbreak", "bypass"
        ],
        env="BLOCKED_KEYWORDS"
    )
    
    # Search Configuration
    MAX_SEARCH_RESULTS: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    SIMILARITY_THRESHOLD: float = Field(default=0.6, env="SIMILARITY_THRESHOLD")
    
    # Session Management
    SESSION_TIMEOUT: int = Field(default=1800, env="SESSION_TIMEOUT")  # 30 minutes
    MAX_CONVERSATION_HISTORY: int = Field(default=10, env="MAX_CONVERSATION_HISTORY")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
