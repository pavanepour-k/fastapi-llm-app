"""
Configuration management following FastAPI settings best practices
Reference: https://fastapi.tiangolo.com/advanced/settings/
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings for type validation
    and automatic environment variable loading.
    
    Single Responsibility: Centralized configuration management
    """
    
    # Application settings
    app_name: str = "LLM Chat Application"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./app.db"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM settings
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    # Vector store settings
    faiss_index_path: str = "data/faiss_index"
    embedding_model: str = "all-mpnet-base-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
