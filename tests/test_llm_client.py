from unittest.mock import MagicMock

import pytest

from asrserve.agents.llm_client import AnthropicClient, GroqClient, OpenAIClient, build_client
from asrserve.config import Settings


def test_build_client_missing_openai_key_raises():
    settings = Settings(llm_provider="openai", openai_api_key=None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_client(settings)


def test_build_client_missing_anthropic_key_raises():
    settings = Settings(llm_provider="anthropic", anthropic_api_key=None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        build_client(settings)


def test_build_client_missing_groq_key_raises():
    settings = Settings(llm_provider="groq", groq_api_key=None)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        build_client(settings)


def test_build_client_selects_openai():
    settings = Settings(llm_provider="openai", openai_api_key="sk-test")
    client = build_client(settings)
    assert isinstance(client, OpenAIClient)


def test_build_client_selects_anthropic():
    settings = Settings(llm_provider="anthropic", anthropic_api_key="sk-ant-test")
    client = build_client(settings)
    assert isinstance(client, AnthropicClient)


def test_build_client_selects_groq():
    settings = Settings(llm_provider="groq", groq_api_key="gsk-test")
    client = build_client(settings)
    assert isinstance(client, GroqClient)
    assert client._client.base_url.host == "api.groq.com"


def test_openai_client_parses_plain_text(monkeypatch):
    client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")

    mock_message = MagicMock(content="hello world")
    mock_choice = MagicMock(message=mock_message)
    mock_usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    mock_resp = MagicMock(choices=[mock_choice], usage=mock_usage)
    client._client.chat.completions.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user")

    assert result.text == "hello world"
    assert result.structured is None
    assert result.provider == "openai"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


def test_openai_client_parses_structured_json():
    client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")

    mock_message = MagicMock(content='{"action_items": []}')
    mock_choice = MagicMock(message=mock_message)
    mock_resp = MagicMock(choices=[mock_choice], usage=None)
    client._client.chat.completions.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user", json_schema={"type": "object"})

    assert result.structured == {"action_items": []}
    assert result.input_tokens == 0


def test_anthropic_client_parses_tool_use():
    client = AnthropicClient(api_key="sk-ant-test", model="claude-haiku-4-5-20251001")

    tool_block = MagicMock(type="tool_use", input={"action_items": [{"task": "x"}]})
    mock_usage = MagicMock(input_tokens=20, output_tokens=8)
    mock_resp = MagicMock(content=[tool_block], usage=mock_usage)
    client._client.messages.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user", json_schema={"type": "object"})

    assert result.structured == {"action_items": [{"task": "x"}]}
    assert result.provider == "anthropic"
    assert result.input_tokens == 20


def test_groq_client_parses_plain_text():
    client = GroqClient(api_key="gsk-test", model="llama-3.3-70b-versatile")

    mock_message = MagicMock(content="- decision made", tool_calls=None)
    mock_choice = MagicMock(message=mock_message)
    mock_usage = MagicMock(prompt_tokens=15, completion_tokens=6)
    mock_resp = MagicMock(choices=[mock_choice], usage=mock_usage)
    client._client.chat.completions.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user")

    assert result.text == "- decision made"
    assert result.structured is None
    assert result.provider == "groq"
    assert result.input_tokens == 15


def test_groq_client_parses_tool_call_structured_output():
    client = GroqClient(api_key="gsk-test", model="llama-3.3-70b-versatile")

    tool_call = MagicMock()
    tool_call.function.arguments = '{"action_items": [{"task": "x"}]}'
    mock_message = MagicMock(content=None, tool_calls=[tool_call])
    mock_choice = MagicMock(message=mock_message)
    mock_resp = MagicMock(choices=[mock_choice], usage=None)
    client._client.chat.completions.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user", json_schema={"type": "object"})

    assert result.structured == {"action_items": [{"task": "x"}]}
    call_kwargs = client._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["tools"][0]["function"]["name"] == "extraction"


def test_anthropic_client_parses_plain_text():
    client = AnthropicClient(api_key="sk-ant-test", model="claude-haiku-4-5-20251001")

    text_block = MagicMock(type="text", text="a summary")
    mock_usage = MagicMock(input_tokens=12, output_tokens=4)
    mock_resp = MagicMock(content=[text_block], usage=mock_usage)
    client._client.messages.create = MagicMock(return_value=mock_resp)

    result = client.complete("system", "user")

    assert result.text == "a summary"
    assert result.structured is None
