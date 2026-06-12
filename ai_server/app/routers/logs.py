from fastapi import APIRouter

from app.analyze_logs import get_recent_analyze_logs
from app.metrics import get_recent_requests

router = APIRouter()


@router.get("/logs/requests")
def logs_requests(limit: int = 50):
    return {"requests": get_recent_requests(limit)}


@router.get("/logs/analyze")
def logs_analyze(limit: int = 50):
    return {"logs": get_recent_analyze_logs(limit)}
