from unittest.mock import MagicMock

from asrserve.agents.assistant import Assistant
from asrserve.agents.llm_client import LLMResponse


def _fake_client(response: LLMResponse) -> MagicMock:
    client = MagicMock()
    client.complete.return_value = response
    return client


def test_load_case_team_copilot_config():
    fake = _fake_client(LLMResponse("ok", None, "openai", "gpt-4o-mini", 0, 0))
    assistant = Assistant.load("case_team_copilot", client=fake)
    assert assistant._config["name"] == "case-team-copilot"
    assert "summarize" in assistant._config["tasks"]
    assert "extract_action_items" in assistant._config["tasks"]


def test_run_task_summarize_uses_configured_template():
    fake = _fake_client(LLMResponse("- point one", None, "openai", "gpt-4o-mini", 5, 5))
    assistant = Assistant.load("case_team_copilot", client=fake)

    result = assistant.run_task("summarize", transcript="client wants X")

    assert result.text == "- point one"
    call_kwargs = fake.complete.call_args.kwargs
    assert "client wants X" in call_kwargs["user_prompt"]
    assert call_kwargs["json_schema"] is None


def test_run_task_action_items_passes_schema():
    fake = _fake_client(LLMResponse("", {"action_items": []}, "openai", "gpt-4o-mini", 5, 5))
    assistant = Assistant.load("case_team_copilot", client=fake)

    result = assistant.run_task("extract_action_items", transcript="Bob will send the report")

    assert result.structured == {"action_items": []}
    call_kwargs = fake.complete.call_args.kwargs
    assert call_kwargs["json_schema"] is not None
    assert call_kwargs["json_schema"]["required"] == ["action_items"]
