from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4.1-mini"
    azure_openai_api_version: str = "2024-05-01-preview"

    # Weather API
    openweather_api_key: str = ""

    # App Settings
    start_location: str = "Geneva"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    # Cache Settings
    cache_enabled: bool = True
    weather_cache_hours: int = 6
    snow_cache_hours: int = 12
    transport_cache_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
