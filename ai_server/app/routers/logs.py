from fastapi import APIRouter

from app.analyze_logs import count_analyze_logs, get_recent_analyze_logs
from app.metrics import count_requests, get_recent_requests

router = APIRouter()


@router.get("/logs/requests")
def logs_requests(limit: int = 50, offset: int = 0):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {
        "requests": get_recent_requests(limit=limit, offset=offset),
        "total": count_requests(),
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/analyze")
def logs_analyze(limit: int = 50, offset: int = 0):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {
        "logs": get_recent_analyze_logs(limit=limit, offset=offset),
        "total": count_analyze_logs(),
        "limit": limit,
        "offset": offset,
    }
