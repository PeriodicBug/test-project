from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "FastAPI Application"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Settings
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 100
    API_RATE_LIMIT_PERIOD: int = 60
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Redis Settings (Optional)
    REDIS_URL: Optional[str] = None
    REDIS_CACHE_TTL: int = 300
    
    # Email Settings (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None
    
    # AWS Settings (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Sentry Settings (Optional)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"]
    UPLOAD_DIR: str = "uploads"
    
    # Worker Settings
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Feature Flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_PASSWORD_RESET: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_METRICS: bool = True
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    def get_database_url(self) -> str:
        """Get the database URL with proper formatting"""
        return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.ENVIRONMENT.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This function uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


settings = get_settings()