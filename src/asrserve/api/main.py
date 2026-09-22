import logging

from fastapi import FastAPI

from asrserve.api.middleware import request_context_middleware
from asrserve.api.routes import agent, health, transcribe
from asrserve.monitoring.metrics import instrument

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="asrserve",
    description="Voice intelligence platform: ASR transcription + LLM agent layer",
    version="0.1.0",
)

app.middleware("http")(request_context_middleware)
instrument(app)

app.include_router(health.router, tags=["health"])
app.include_router(transcribe.router, tags=["transcribe"])
app.include_router(agent.router, tags=["agent"])
