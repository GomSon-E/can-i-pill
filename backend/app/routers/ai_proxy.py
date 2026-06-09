import os
import httpx
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://ai-server:8001")


def _make_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ""


@router.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    async with _make_client() as client:
        response = await client.post(
            f"{AI_SERVER_URL}/ocr",
            files={"image": (image.filename, await image.read(), image.content_type)},
        )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/label")
async def label(image: UploadFile = File(...)):
    async with _make_client() as client:
        response = await client.post(
            f"{AI_SERVER_URL}/label",
            files={"image": (image.filename, await image.read(), image.content_type)},
        )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/analyze")
async def analyze(body: AnalyzeRequest):
    async with _make_client() as client:
        response = await client.post(
            f"{AI_SERVER_URL}/analyze",
            json={"question": body.question, "context": body.context},
        )
    return JSONResponse(content=response.json(), status_code=response.status_code)
