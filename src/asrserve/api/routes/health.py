from fastapi import APIRouter, Depends

from asrserve.api.deps import get_settings_dep
from asrserve.api.schemas import HealthResponse
from asrserve.config import Settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        asr_model_size=settings.asr_model_size,
        llm_provider=settings.llm_provider,
    )
