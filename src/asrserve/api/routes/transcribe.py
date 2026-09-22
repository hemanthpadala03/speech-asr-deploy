import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from asrserve.api.deps import get_asr_dep
from asrserve.api.schemas import TranscribeResponse
from asrserve.inference.model import WhisperASR
from asrserve.inference.postprocess import to_srt

router = APIRouter()

_ALLOWED_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile, asr: WhisperASR = Depends(get_asr_dep)) -> TranscribeResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported audio type '{suffix}'. Allowed: {sorted(_ALLOWED_SUFFIXES)}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = asr.transcribe(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return TranscribeResponse(text=result.text, language=result.language, srt=to_srt(result))
