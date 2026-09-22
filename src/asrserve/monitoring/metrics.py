from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def instrument(app: FastAPI) -> None:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
