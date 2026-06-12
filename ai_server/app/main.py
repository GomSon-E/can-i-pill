import logging

from fastapi import FastAPI
from app.routers import ai, logs, metrics

logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(ai.router)
app.include_router(metrics.router)
app.include_router(logs.router)
