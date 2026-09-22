"""faster-whisper wrapper.

CTranslate2-backed Whisper inference -- no torch dependency, runs int8 on
CPU fast enough for a demo/interview setting without a GPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from asrserve.config import Settings, get_settings


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str
    segments: list[TranscriptSegment] = field(default_factory=list)


class WhisperASR:
    def __init__(self, model_size: str, device: str, compute_type: str):
        from faster_whisper import WhisperModel

        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        segments, info = self._model.transcribe(audio_path, beam_size=5)
        seg_list = [
            TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in segments
        ]
        full_text = " ".join(s.text for s in seg_list).strip()
        return TranscriptionResult(text=full_text, language=info.language, segments=seg_list)


@lru_cache
def get_asr(settings: Settings | None = None) -> WhisperASR:
    settings = settings or get_settings()
    return WhisperASR(settings.asr_model_size, settings.asr_device, settings.asr_compute_type)
