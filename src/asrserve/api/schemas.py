from pydantic import BaseModel


class TranscribeResponse(BaseModel):
    text: str
    language: str
    srt: str


class SummarizeRequest(BaseModel):
    transcript: str
    prompt_version: str = "meeting_summary_v2"


class SummarizeResponse(BaseModel):
    summary: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


class ActionItem(BaseModel):
    task: str
    owner: str
    due: str | None
    confidence: str


class ActionItemsResponse(BaseModel):
    action_items: list[ActionItem]
    provider: str
    model: str


class HealthResponse(BaseModel):
    status: str
    asr_model_size: str
    llm_provider: str
