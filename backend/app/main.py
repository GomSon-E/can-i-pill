from fastapi import FastAPI
from app.routers import user, health as health_router, prescriptions, supplements, history, mock_ai

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(user.router)
app.include_router(health_router.router)
app.include_router(prescriptions.router)
app.include_router(supplements.router)
app.include_router(history.router)
app.include_router(mock_ai.router)
