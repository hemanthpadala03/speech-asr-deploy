from functools import lru_cache

from asrserve.agents.assistant import Assistant
from asrserve.agents.llm_client import LLMClient, build_client
from asrserve.config import Settings, get_settings
from asrserve.inference.model import WhisperASR, get_asr


def get_settings_dep() -> Settings:
    return get_settings()


def get_asr_dep() -> WhisperASR:
    return get_asr()


@lru_cache
def get_llm_client_dep() -> LLMClient:
    return build_client()


@lru_cache
def get_case_team_copilot() -> Assistant:
    return Assistant.load("case_team_copilot", client=get_llm_client_dep())
