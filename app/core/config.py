"""Configuration settings for the Starluck Astro FastAPI application."""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    app_name: str = "Starluck Astro API"
    app_version: str = "1.0.0"
    debug: bool = False
    api_base_url: str = "http://localhost:8000/api/v1"
    enable_debug_outputs: bool = False
    
    # Security Configuration
    allowed_hosts: List[str] = ["127.0.0.1", "localhost"]
    api_key: Optional[str] = None
    enable_api_key_auth: bool = False
    
    # Swiss Ephemeris Configuration
    swe_path: Optional[str] = None
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:8001", "http://127.0.0.1:8001"]
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @field_validator("cors_origins", mode="before") 
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "STARLUCK_"

settings = Settings()