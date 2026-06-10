import json
import os

import httpx
from google.genai import types


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


_VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_relevant": {"type": "boolean"},
        "is_clear": {"type": "boolean"},
        "items": {"type": "array", "items": {"type": "string"}},
        "missing_info": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["is_relevant", "is_clear", "items", "missing_info"],
}


def _generate_validation(question: str) -> dict:
    from app.routers.ai import MODEL, _client

    prompt = (
        "약, 영양제, 음식 상호작용 분석 서비스의 질문인지 검증하세요. "
        "반드시 JSON으로만 답하세요.\n"
        f"질문: {question}"
    )
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_VALIDATION_SCHEMA,
        ),
    )
    return json.loads(response.text)


def validate_query(question: str) -> dict:
    data = _generate_validation(question)
    return {
        "is_relevant": bool(data.get("is_relevant")),
        "is_clear": bool(data.get("is_clear")),
        "items": data.get("items") or [],
        "missing_info": data.get("missing_info") or [],
    }


def _fetch_backend_data():
    with httpx.Client(base_url=BACKEND_URL) as client:
        prescriptions_resp = client.get("/prescriptions")
        supplements_resp = client.get("/supplements")
        health_resp = client.get("/health-info")

    prescriptions = (
        prescriptions_resp.json().get("prescriptions", [])
        if prescriptions_resp.status_code == 200
        else []
    )
    supplements = (
        supplements_resp.json().get("supplements", [])
        if supplements_resp.status_code == 200
        else []
    )
    health = health_resp.json() if health_resp.status_code == 200 else {}

    return prescriptions, supplements, health


def gather_context() -> dict:
    prescriptions, supplements, health = _fetch_backend_data()

    drugs = [
        drug["name"]
        for prescription in prescriptions
        for drug in prescription.get("drugs", [])
    ]
    normalized_supplements = [
        {"name": s["name"], "ingredients": s.get("ingredients", [])}
        for s in supplements
    ]

    return {
        "drugs": drugs,
        "supplements": normalized_supplements,
        "health_conditions": health.get("conditions", []),
        "allergies": health.get("allergies", []),
    }


def ask_clarification(reason: str) -> dict:
    return {"clarification_prompt": reason}
