import io
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from asrserve.agents.assistant import Assistant
from asrserve.agents.llm_client import LLMResponse
from asrserve.api.deps import get_asr_dep, get_case_team_copilot, get_settings_dep
from asrserve.api.main import app
from asrserve.config import Settings
from asrserve.inference.model import TranscriptionResult, TranscriptSegment


def test_health_endpoint():
    app.dependency_overrides[get_settings_dep] = lambda: Settings(
        llm_provider="openai", openai_api_key="sk-test", asr_model_size="tiny"
    )
    client = TestClient(app)
    resp = client.get("/health")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["asr_model_size"] == "tiny"


def test_transcribe_endpoint_rejects_unsupported_type():
    # FastAPI resolves all endpoint dependencies before running the body, so
    # even though this request never reaches asr.transcribe(), the
    # WhisperASR dependency still gets constructed unless overridden --
    # override it here to keep this a fast, network-free unit test.
    app.dependency_overrides[get_asr_dep] = lambda: MagicMock()
    client = TestClient(app)
    resp = client.post("/transcribe", files={"file": ("notes.txt", io.BytesIO(b"hi"), "text/plain")})
    app.dependency_overrides.clear()
    assert resp.status_code == 400


def test_transcribe_endpoint_returns_text_and_srt():
    fake_asr = MagicMock()
    fake_asr.transcribe.return_value = TranscriptionResult(
        text="hello world",
        language="en",
        segments=[TranscriptSegment(start=0.0, end=1.2, text="hello world")],
    )
    app.dependency_overrides[get_asr_dep] = lambda: fake_asr
    client = TestClient(app)

    resp = client.post("/transcribe", files={"file": ("clip.wav", io.BytesIO(b"fake audio bytes"), "audio/wav")})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["text"] == "hello world"
    assert body["language"] == "en"
    assert "00:00:00,000 --> 00:00:01,200" in body["srt"]


def test_agent_summarize_endpoint():
    fake_client = MagicMock()
    fake_client.complete.return_value = LLMResponse("- decision made", None, "openai", "gpt-4o-mini", 10, 6)
    app.dependency_overrides[get_case_team_copilot] = lambda: Assistant.load(
        "case_team_copilot", client=fake_client
    )
    client = TestClient(app)

    resp = client.post("/agent/summarize", json={"transcript": "we approved the budget"})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == "- decision made"
    assert body["provider"] == "openai"


def test_agent_action_items_endpoint():
    fake_client = MagicMock()
    fake_client.complete.return_value = LLMResponse(
        "",
        {"action_items": [{"task": "Send report", "owner": "James", "due": "Friday", "confidence": "high"}]},
        "openai",
        "gpt-4o-mini",
        10,
        6,
    )
    app.dependency_overrides[get_case_team_copilot] = lambda: Assistant.load(
        "case_team_copilot", client=fake_client
    )
    client = TestClient(app)

    resp = client.post("/agent/action-items", json={"transcript": "James will send the report Friday"})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["action_items"]) == 1
    assert body["action_items"][0]["owner"] == "James"
