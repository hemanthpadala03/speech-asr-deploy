from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Literal["openai", "anthropic", "groq"] = "openai"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"

    asr_model_size: str = "small"
    asr_device: str = "cpu"
    asr_compute_type: str = "int8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
