"""Provider-agnostic LLM client.

A case team today might be on OpenAI, tomorrow on Claude via an enterprise
Anthropic contract, and asking to swap should not mean rewriting every prompt
call site. This wraps both behind one interface so the rest of the codebase
(``pipeline.py``, ``eval.py``, the API routes) never imports a provider SDK
directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from asrserve.config import Settings, get_settings


@dataclass
class LLMResponse:
    text: str
    structured: dict[str, Any] | None
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse: ...


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {}
        if json_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "extraction", "schema": json_schema, "strict": True},
            }

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        text = resp.choices[0].message.content or ""
        structured = json.loads(text) if json_schema is not None else None
        return LLMResponse(
            text=text,
            structured=structured,
            provider="openai",
            model=self._model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
        )


class AnthropicClient:
    def __init__(self, api_key: str, model: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        tools = None
        tool_choice = None
        if json_schema is not None:
            tools = [{"name": "extraction", "description": "Return the extracted structured data.", "input_schema": json_schema}]
            tool_choice = {"type": "tool", "name": "extraction"}

        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            **kwargs,
        )

        structured = None
        text = ""
        for block in resp.content:
            if block.type == "tool_use":
                structured = block.input
            elif block.type == "text":
                text += block.text

        return LLMResponse(
            text=text,
            structured=structured,
            provider="anthropic",
            model=self._model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )


class GroqClient:
    """Groq's API is OpenAI-compatible at the transport level (same SDK,
    different base_url), but its structured-output support ("response_format":
    "json_schema") is inconsistent across models -- function/tool calling is
    the one structured-output path Groq reliably supports everywhere, so this
    uses that instead of reusing OpenAIClient's json_schema branch.
    """

    _BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=self._BASE_URL)
        self._model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {}
        if json_schema is not None:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "extraction",
                        "description": "Return the extracted structured data.",
                        "parameters": json_schema,
                    },
                }
            ]
            kwargs["tool_choice"] = {"type": "function", "function": {"name": "extraction"}}

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        message = resp.choices[0].message
        structured = None
        if message.tool_calls:
            structured = json.loads(message.tool_calls[0].function.arguments)
        return LLMResponse(
            text=message.content or "",
            structured=structured,
            provider="groq",
            model=self._model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
        )


def build_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("LLM_PROVIDER=groq but GROQ_API_KEY is not set")
        return GroqClient(settings.groq_api_key, settings.groq_model)
    if not settings.openai_api_key:
        raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
    return OpenAIClient(settings.openai_api_key, settings.openai_model)
