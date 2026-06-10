import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.metrics import get_metrics_summary

router = APIRouter()

_DASHBOARD_HTML_PATH = os.path.join(os.path.dirname(__file__), "../static/dashboard.html")


@router.get("/metrics")
def metrics():
    return get_metrics_summary()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open(_DASHBOARD_HTML_PATH) as f:
        return f.read()
