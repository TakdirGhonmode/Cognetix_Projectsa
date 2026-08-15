import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "SaaS Backend Platform"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-jwt-key-for-saas-platform-change-in-production-32bytes")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Configuration (MySQL configured with user password, fallback to SQLite if offline)
    # Password 'Takdir@1234' URL-encoded as 'Takdir%401234'
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:Takdir%401234@localhost:3306/saas_db"
    )
    
    # Subscription Tiers & Feature Matrix
    TIER_LIMITS: dict = {
        "free": {
            "max_users": 3,
            "max_alerts": 10,
            "max_projects": 2,
            "max_api_calls_per_day": 100,
            "has_analytics": False,
            "has_export": False,
            "price_monthly": 0.0
        },
        "basic": {
            "max_users": 10,
            "max_alerts": 100,
            "max_projects": 15,
            "max_api_calls_per_day": 1000,
            "has_analytics": True,
            "has_export": False,
            "price_monthly": 29.99
        },
        "premium": {
            "max_users": 100,
            "max_alerts": 999999,
            "max_projects": 100,
            "max_api_calls_per_day": 100000,
            "has_analytics": True,
            "has_export": True,
            "price_monthly": 99.99
        }
    }

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
