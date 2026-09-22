from fastapi import APIRouter, Depends

from asrserve.agents.assistant import Assistant
from asrserve.api.deps import get_case_team_copilot
from asrserve.api.schemas import (
    ActionItem,
    ActionItemsResponse,
    SummarizeRequest,
    SummarizeResponse,
)

router = APIRouter()


@router.post("/agent/summarize", response_model=SummarizeResponse)
def summarize(
    body: SummarizeRequest, copilot: Assistant = Depends(get_case_team_copilot)
) -> SummarizeResponse:
    resp = copilot.run_task("summarize", transcript=body.transcript)
    return SummarizeResponse(
        summary=resp.text,
        provider=resp.provider,
        model=resp.model,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
    )


@router.post("/agent/action-items", response_model=ActionItemsResponse)
def extract_action_items(
    body: SummarizeRequest, copilot: Assistant = Depends(get_case_team_copilot)
) -> ActionItemsResponse:
    resp = copilot.run_task("extract_action_items", transcript=body.transcript)
    items = [ActionItem(**item) for item in (resp.structured or {}).get("action_items", [])]
    return ActionItemsResponse(action_items=items, provider=resp.provider, model=resp.model)
