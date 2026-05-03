from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "PixelForge"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 1349
    workers: int = 1
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./pixelforge.db"
    
    # Storage
    storage_path: str = "./storage"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    
    # Security
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # AI Models
    ai_models_path: str = "./models"
    ai_default_model_tier: str = "balanced"  # fast/light, balanced, best_quality
    ai_use_gpu: bool = False
    ai_max_model_memory_mb: int = 1024  # 1GB max for models
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_minutes: int = 1
    
    # Analytics (opt-in)
    analytics_enabled: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()