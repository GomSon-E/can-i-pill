from fastapi import FastAPI
from app.routers import ai, metrics

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(ai.router)
app.include_router(metrics.router)
