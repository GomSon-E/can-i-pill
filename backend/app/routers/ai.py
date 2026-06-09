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


@router.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    image_bytes = await image.read()
    prompt = """이 처방전 이미지에서 약품 정보를 추출해주세요.
반드시 아래 JSON 형식으로만 응답하세요:
{
  "name": "처방전 이름 (병원명 + 날짜, 예: 내과 처방전 2026-05)",
  "drugs": [
    {
      "name": "약품명",
      "dosage": "용량 (예: 500mg)",
      "frequency": "복용 횟수 (예: 1일 2회)",
      "days": 30,
      "usage": "복용 방법 (예: 식후)",
      "cautions": "주의사항"
    }
  ]
}"""
    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


@router.post("/label")
async def label(image: UploadFile = File(...)):
    image_bytes = await image.read()
    prompt = """이 영양제 라벨 이미지에서 제품명과 영양 성분을 추출해주세요.
절대 함량만 추출하고 (비율 % 제외), 천 단위 쉼표는 제거하세요.
반드시 아래 JSON 형식으로만 응답하세요:
{
  "name": "제품명",
  "nutrients": [
    {
      "ingredient": "성분명",
      "amount": "함량 숫자 (문자열)",
      "unit": "단위 (mg, g, mcg 등)"
    }
  ]
}"""
    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=image.content_type or "image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    prompt = f"""당신은 약사와 의사 역할을 합니다. 아래 질문에 대해 약물·영양제·음식 상호작용을 분석해주세요.

질문: {body.question}
컨텍스트: {body.context}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "level": "safe 또는 caution 또는 danger 중 정확히 하나",
  "doctorOpinion": {{
    "summary": "의사 관점 한 줄 요약",
    "detail": "의사 관점 상세 설명"
  }},
  "pharmacistOpinion": {{
    "summary": "약사 관점 한 줄 요약",
    "detail": "약사 관점 상세 설명"
  }},
  "alternatives": ["대안 약품 또는 성분 (없으면 빈 배열)"]
}}

level 기준:
- safe: 함께 복용해도 안전한 경우
- caution: 주의가 필요하지만 복용 가능한 경우
- danger: 함께 복용하면 위험한 경우"""

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            response = _client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(response.text)
            if data.get("level") not in ("safe", "caution", "danger"):
                continue
            return data
        except Exception as e:
            last_exc = e

    raise last_exc
