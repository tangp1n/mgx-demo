"""Configuration management for the application."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    mongodb_url: str = "mongodb://localhost:27017/appbuilder"
    mongodb_database: str = "appbuilder"

    # Security
    secret_key: str = "change-me-in-production"
    session_expiry_hours: int = 24

    # LLM Configuration
    llm_provider: str = "openai"  # openai or anthropic
    llm_model: str = "gpt-4"  # 默认模型，可通过 LLM_MODEL 环境变量配置

    # OpenAI Configuration
    openai_api_key: Optional[str] = None  # 通过 OPENAI_API_KEY 环境变量配置
    openai_base_url: Optional[str] = None  # 自定义 OpenAI API base URL，通过 OPENAI_BASE_URL 环境变量配置
    openai_model: Optional[str] = None  # OpenAI 专用模型，通过 OPENAI_MODEL 环境变量配置（可选，未设置时使用 llm_model）

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None  # 通过 ANTHROPIC_API_KEY 环境变量配置
    anthropic_model: Optional[str] = None  # Anthropic 专用模型，通过 ANTHROPIC_MODEL 环境变量配置（可选，未设置时使用 llm_model）

    # Container Configuration
    docker_network: str = "appbuilder-network"
    container_memory_limit_mb: int = 512
    container_cpu_limit: float = 0.5
    container_timeout_minutes: int = 60

    # Server
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    api_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()

