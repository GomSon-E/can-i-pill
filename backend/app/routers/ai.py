import os
import json
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.db import _load_env

_load_env()

router = APIRouter()

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.1-flash-lite"


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ''


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
    image_bytes = await image.read()
    prompt = _OCR_PROMPT
    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
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
    image_bytes = await image.read()
    prompt = _LABEL_PROMPT
    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_LABEL_SCHEMA,
        ),
    )
    return _normalize_label_result(json.loads(response.text))


_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "level": {"type": "string", "enum": ["safe", "caution", "danger"]},
        "doctorOpinion": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["summary", "detail"],
        },
        "pharmacistOpinion": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["summary", "detail"],
        },
        "alternatives": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["level", "doctorOpinion", "pharmacistOpinion", "alternatives"],
}

_ANALYSIS_RULES = (
    "당신은 50~60대 사용자를 돕는 약물·영양제·음식 상호작용 안내 도우미입니다.\n"
    "아래 사용자의 약물 프로필과 질문을 바탕으로, 질문한 항목을 함께 드셔도 되는지 판단하세요.\n"
    "\n"
    "[판단 규칙]\n"
    "- level은 반드시 'safe' / 'caution' / 'danger' 중 하나로만.\n"
    "- 등급 정의:\n"
    "  · danger(위험): 함께 섭취를 피해야 하는 급성·심각 위해. 출혈, 심장 리듬 이상(QT 연장·부정맥), "
    "세로토닌 증후군, 혈압 급상승, 심한 간·신장 손상처럼 되돌리기 어렵거나 생명에 위협이 될 수 있는 경우.\n"
    "  · caution(주의): 복용 시간 간격을 두거나 양·복용법을 조절하면 관리되는 경우. "
    "흡수율 저하(약효 감소), 경미~중등도 부작용 증가 등 → 회피가 아니라 '시간 띄우기·모니터링'으로 대응.\n"
    "  · safe(안전): 알려진 상호작용이 전혀 없고 일반적인 섭취량에서 문제되지 않는 경우.\n"
    "- [중요 정책] 이 서비스는 상호작용 '경고' 도우미입니다. 근거상 어떤 상호작용이라도 있으면 "
    "(흡수율 저하처럼 시간 간격으로 관리되는 경미한 것 포함) **최소 caution**으로 안내하세요. "
    "safe는 알려진 상호작용이 전혀 없을 때만 사용합니다.\n"
    "- 위험을 과소평가하지 마세요. 단, 시간 간격으로 관리되는 흡수저하 등을 danger로 과장하지도 마세요"
    "(이런 경우는 caution). 정말 애매하면 한 단계 보수적으로 판단.\n"
    "[작성 규칙]\n"
    "- 어려운 의학용어 금지. 50~60대가 바로 이해할 쉬운 말로.\n"
    "- 각 summary는 한 문장(40자 이내). 각 detail은 2~4문장.\n"
    "- doctorOpinion은 몸에 생길 수 있는 변화 중심, pharmacistOpinion은 복용 방법·시간 간격 중심.\n"
    "- 진단·처방이 아니며 증상이 있으면 의사·약사와 상담하라는 취지를 detail에 자연스럽게 포함.\n"
    "- alternatives는 더 안전한 대체 식품/영양제 0~3개. safe면 빈 배열도 가능.\n"
    "- 추측성 수치나 출처 불명 정보 금지.\n"
)


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    context_section = f"\n[사용자 프로필 및 복용 약]\n{body.context}" if body.context else ""
    prompt = f"{_ANALYSIS_RULES}{context_section}\n\n[질문]\n\"{body.question}\""

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            response = _client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_ANALYSIS_SCHEMA,
                ),
            )
            data = json.loads(response.text)
            if data.get("level") not in ("safe", "caution", "danger"):
                continue
            return data
        except Exception as e:
            last_exc = e

    raise last_exc
