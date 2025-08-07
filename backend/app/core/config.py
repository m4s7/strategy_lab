from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Strategy Lab API"
    debug: bool = False
    environment: str = "development"
    log_level: str = "info"
    version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./data/strategy_lab.db"
    database_echo: bool = False  # Set to True for SQL logging
    
    # Security settings (will be used later)
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Create global settings instance
settings = Settings()