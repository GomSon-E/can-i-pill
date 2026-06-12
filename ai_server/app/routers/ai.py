import asyncio
import functools
import os
import json
import logging
import time
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.analyze_logs import record_analyze_log
from app.concurrency import GEMINI_EXECUTOR, GEMINI_SEMAPHORE
from app.metrics import record_metric
from app.harness import harness
from app.mock_responses import MOCK_OCR_RESPONSE, MOCK_LABEL_RESPONSE, MOCK_ANALYZE_RESPONSE


def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), "../../../.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


_load_env()

router = APIRouter()
logger = logging.getLogger(__name__)

AI_MOCK_MODE = os.environ.get("AI_MOCK_MODE", "").lower() == "true"

if AI_MOCK_MODE:
    _client = None
else:
    _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.1-flash-lite"


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ''


def _record_gemini_metric(endpoint: str, start: float, exc: Exception | None = None) -> float:
    latency_ms = (time.monotonic() - start) * 1000
    if exc is None:
        record_metric(endpoint, 200, latency_ms, True)
    else:
        status_code = getattr(exc, "code", None) or 500
        record_metric(endpoint, status_code, latency_ms, False)
    return latency_ms


_OCR_PROMPT = (
    "이 처방전 이미지에서 처방의약품 관련 정보만 추출하세요.\n"
    "규칙:\n"
    "- 질환명, 질병분류기호, 각 의약품의 약품명, 1회투약량, 1일투여횟수, 총투약일수, 용법, 주의사항만 추출\n"
    "- 병원명, 주소, 전화번호, 환자 개인정보, 서명란, 약국사용란, 일반 안내문구는 제외\n"
    "- 약품명은 보이는 한글/영문/용량 표기를 가능한 그대로 유지\n"
    "- 읽히지 않는 부분은 추측하지 말고 생략\n"
    "- 처방의약품 정보가 전혀 없으면 drugs를 빈 배열로 반환\n"
    "\n"
    "반드시 아래 JSON 형식으로만 응답하세요:\n"
    '{\n'
    '  "name": "병원명 + 날짜 (예: 연세내과의원 2026-05)",\n'
    '  "drugs": [\n'
    '    {\n'
    '      "name": "약품명",\n'
    '      "dosage": "1회투약량 (예: 1정, 500mg)",\n'
    '      "frequency": "1일투여횟수 (예: 1일 2회)",\n'
    '      "days": 30,\n'
    '      "usage": "용법 (예: 식후 30분)",\n'
    '      "cautions": "주의사항 (없으면 빈 문자열)"\n'
    '    }\n'
    '  ]\n'
    '}'
)


@router.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    if AI_MOCK_MODE:
        return MOCK_OCR_RESPONSE
    image_bytes = await image.read()
    start = time.monotonic()
    try:
        async with GEMINI_SEMAPHORE:
            response = await asyncio.get_running_loop().run_in_executor(
                GEMINI_EXECUTOR,
                functools.partial(
                    _client.models.generate_content,
                    model=MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
                        _OCR_PROMPT,
                    ],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                ),
            )
    except Exception as e:
        _record_gemini_metric("/ocr", start, e)
        raise
    _record_gemini_metric("/ocr", start)
    return json.loads(response.text)


_LABEL_PROMPT = (
    "이 이미지에서 화면 표시용 영양제명과 영양성분·함량(절대량)만 추출하세요.\n"
    "규칙:\n"
    "- name은 화면에 표시할 대표명입니다. 제품명이 보이면 제품명을 그대로 사용\n"
    "- 제품명이 보이지 않거나 일부만 읽히면 대표 성분명으로 '비타민C 영양제', '마그네슘 영양제'처럼 생성\n"
    "- name은 가능하면 비우지 말고, 브랜드·제조사명이 아니라 사용자가 식별할 수 있는 영양제명/대표명으로 작성\n"
    "- 절대 함량(mg, μg, g, IU 등 실제 양)만 포함\n"
    "- 비율(%)은 모두 제외 (1일 영양성분기준치 %, 함량 옆에 괄호로 적힌 % 등)\n"
    "- 숫자 사이 천 단위 쉼표는 제거 (예: '1,000' → '1000', '4,917' → '4917')\n"
    "- 영양성분/기능성분/지표성분만 포함, 브랜드·제조사·주의사항·보관방법 등은 무시\n"
    "- 함량이 0인 항목(열량 0kcal, 단백질 0g, 지방 0g, 탄수화물 0g, 나트륨 0mg)은 제외\n"
    "- 영양성분 정보가 없으면 nutrients를 빈 배열로 반환\n"
    "\n"
    "반드시 아래 JSON 형식으로만 응답하세요:\n"
    '{\n'
    '  "name": "화면 표시용 영양제명 또는 대표명",\n'
    '  "nutrients": [\n'
    '    {\n'
    '      "ingredient": "성분명",\n'
    '      "amount": "함량 숫자 (문자열, 단위 제외)",\n'
    '      "unit": "단위 (mg, g, mcg, IU 등)"\n'
    '    }\n'
    '  ]\n'
    '}'
)

_LABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "nutrients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ingredient": {"type": "string"},
                    "amount": {"type": "string"},
                    "unit": {"type": "string"},
                },
                "required": ["ingredient", "amount", "unit"],
            },
        },
        "ingredients": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "nutrients"],
}


def _format_nutrient(nutrient: dict) -> str:
    ingredient = str(nutrient.get("ingredient", "")).strip()
    amount = str(nutrient.get("amount", "")).strip()
    unit = str(nutrient.get("unit", "")).strip()
    if ingredient and amount and unit:
        return f"{ingredient} {amount}{unit}"
    if ingredient:
        return ingredient
    return ""


def _build_label_display_name(data: dict) -> str:
    name = str(data.get("name", "")).strip()
    if name:
        return name

    nutrients = data.get("nutrients") or []
    ingredient_names = [
        str(nutrient.get("ingredient", "")).strip()
        for nutrient in nutrients
        if isinstance(nutrient, dict) and str(nutrient.get("ingredient", "")).strip()
    ]
    if len(ingredient_names) >= 2:
        return f"{ingredient_names[0]} 외 {len(ingredient_names) - 1}종 영양제"
    if len(ingredient_names) == 1:
        return f"{ingredient_names[0]} 영양제"
    return "알 수 없는 영양제"


def _normalize_label_result(data: dict) -> dict:
    data["name"] = _build_label_display_name(data)
    data["nutrients"] = data.get("nutrients") or []
    data["ingredients"] = [
        formatted
        for nutrient in data["nutrients"]
        if isinstance(nutrient, dict)
        for formatted in [_format_nutrient(nutrient)]
        if formatted
    ]
    return data


@router.post("/label")
async def label(image: UploadFile = File(...)):
    if AI_MOCK_MODE:
        return MOCK_LABEL_RESPONSE
    image_bytes = await image.read()
    start = time.monotonic()
    try:
        async with GEMINI_SEMAPHORE:
            response = await asyncio.get_running_loop().run_in_executor(
                GEMINI_EXECUTOR,
                functools.partial(
                    _client.models.generate_content,
                    model=MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
                        _LABEL_PROMPT,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=_LABEL_SCHEMA,
                    ),
                ),
            )
    except Exception as e:
        _record_gemini_metric("/label", start, e)
        raise
    _record_gemini_metric("/label", start)
    return _normalize_label_result(json.loads(response.text))


@router.post("/analyze")
async def analyze(body: AnalyzeRequest):
    if AI_MOCK_MODE:
        return MOCK_ANALYZE_RESPONSE
    start = time.monotonic()
    try:
        async with GEMINI_SEMAPHORE:
            result = await asyncio.get_running_loop().run_in_executor(
                GEMINI_EXECUTOR, harness.run_agent, body.question, body.context
            )
    except Exception as e:
        _record_gemini_metric("/analyze", start, e)
        raise
    latency_ms = _record_gemini_metric("/analyze", start)

    if "type" not in result:
        result = {"type": "clarification", **result}

    logger.info("analyze result: %s", json.dumps(result, ensure_ascii=False))
    record_analyze_log(body.question, body.context, result, latency_ms)
    return result
