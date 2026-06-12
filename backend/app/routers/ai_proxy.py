import os
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter()

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:8001")

# harness.run_agent()은 self-evaluate 재시도와 다중 항목 병렬 분석으로
# httpx 기본 타임아웃(5초)을 훌쩍 넘길 수 있어 /analyze는 더 긴 타임아웃을 둔다.
ANALYZE_TIMEOUT = 120.0


def _make_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ""


async def _post_to_ai_server(path: str, *, timeout=None, **kwargs) -> httpx.Response:
    client_kwargs = {"timeout": timeout} if timeout is not None else {}
    try:
        async with _make_client(**client_kwargs) as client:
            return await client.post(f"{AI_SERVER_URL}{path}", **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI server connection failed: {exc}",
        ) from exc


async def _get_from_ai_server(path: str, *, timeout=None, **kwargs) -> httpx.Response:
    client_kwargs = {"timeout": timeout} if timeout is not None else {}
    try:
        async with _make_client(**client_kwargs) as client:
            return await client.get(f"{AI_SERVER_URL}{path}", **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI server connection failed: {exc}",
        ) from exc


@router.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    response = await _post_to_ai_server(
        "/ocr",
        files={"image": (image.filename, await image.read(), image.content_type)},
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/label")
async def label(image: UploadFile = File(...)):
    response = await _post_to_ai_server(
        "/label",
        files={"image": (image.filename, await image.read(), image.content_type)},
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/analyze")
async def analyze(body: AnalyzeRequest):
    response = await _post_to_ai_server(
        "/analyze",
        json={"question": body.question, "context": body.context},
        timeout=ANALYZE_TIMEOUT,
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/dashboard")
async def dashboard():
    response = await _get_from_ai_server("/dashboard")
    return HTMLResponse(content=response.content, status_code=response.status_code)


@router.get("/metrics")
async def metrics():
    response = await _get_from_ai_server("/metrics")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/logs/requests")
async def logs_requests(limit: int = 50, offset: int = 0):
    response = await _get_from_ai_server(
        "/logs/requests",
        params={"limit": limit, "offset": offset},
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/logs/analyze")
async def logs_analyze(limit: int = 50, offset: int = 0):
    response = await _get_from_ai_server(
        "/logs/analyze",
        params={"limit": limit, "offset": offset},
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)
