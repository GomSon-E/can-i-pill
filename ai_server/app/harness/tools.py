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
    try:
        with httpx.Client(base_url=BACKEND_URL) as client:
            prescriptions_resp = client.get("/prescriptions")
            supplements_resp = client.get("/supplements")
            health_resp = client.get("/health-info")
    except httpx.RequestError:
        return [], [], {}

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


def _generate_analysis(question: str, context: str) -> dict:
    from app.routers.ai import MODEL, _client, _ANALYSIS_RULES, _ANALYSIS_SCHEMA

    context_section = f"\n[사용자 프로필 및 복용 약]\n{context}" if context else ""
    prompt = f"{_ANALYSIS_RULES}{context_section}\n\n[질문]\n\"{question}\""

    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_ANALYSIS_SCHEMA,
        ),
    )
    return json.loads(response.text)


def analyze(question: str, context: str) -> dict:
    data = {}
    for _ in range(3):
        data = _generate_analysis(question, context)
        if data.get("level") in ("safe", "caution", "danger"):
            return data
    return data


def _generate_item_analysis(item: str, context: str) -> dict:
    from app.routers.ai import MODEL, _client, _ANALYSIS_RULES, _ANALYSIS_SCHEMA

    context_section = f"\n[사용자 프로필 및 복용 약]\n{context}" if context else ""
    prompt = f"{_ANALYSIS_RULES}{context_section}\n\n[분석 대상 항목]\n\"{item}\""

    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_ANALYSIS_SCHEMA,
        ),
    )
    return json.loads(response.text)


def analyze_item(item: str, context: str) -> dict:
    data = {}
    for _ in range(3):
        data = _generate_item_analysis(item, context)
        if data.get("level") in ("safe", "caution", "danger"):
            return {"name": item, **data}
    return {"name": item, **data}


_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "factuality": {"type": "integer"},
                "readability": {"type": "integer"},
                "usefulness": {"type": "integer"},
                "schema": {"type": "integer"},
            },
            "required": ["factuality", "readability", "usefulness", "schema"],
        },
        "rationale": {"type": "string"},
        "jargon_terms_found": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["scores", "rationale", "jargon_terms_found"],
}


_JUDGE_RULES = (
    "당신은 약물 상호작용 안내 답변의 '글 품질'을 평가하는 엄격한 심사위원입니다.\n"
    "아래 질문과 후보 답변(JSON)을 보고 각 항목을 1~5점(정수)으로 채점하세요.\n"
    "※ 위험도 등급(level: safe/caution/danger)의 적정성은 평가하지 마세요(별도 정확도 지표로 측정함). "
    "오직 답변 '본문'의 품질만 보세요.\n"
    "- factuality(사실성/무환각): 약리 상식에 부합하고 날조된 수치·근거나 사실 오류(환각)가 없는가.\n"
    "- readability(가독성): 50~60대가 이해할 쉬운 말인가. 번역 안 된 의학용어가 있으면 감점.\n"
    "- usefulness(유용성): 복용 시간 간격·대안 등 구체적이고 실행 가능한가.\n"
    "- schema(스키마+면책): 의사·약사 소견/대안 형식이 갖춰지고 면책 취지가 있는가.\n"
    "jargon_terms_found에는 답변에서 발견된 어려운 의학용어를 나열하세요(없으면 빈 배열).\n"
    "반드시 JSON으로만 답하세요."
)


def _generate_judge(question: str, candidate: dict) -> dict:
    from app.routers.ai import MODEL, _client

    prompt = (
        f"{_JUDGE_RULES}\n\n"
        f"[질문]\n\"{question}\"\n\n"
        f"[후보 답변]\n{json.dumps(candidate, ensure_ascii=False)}"
    )
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_JUDGE_SCHEMA,
        ),
    )
    return json.loads(response.text)


def reject(reason: str) -> dict:
    return {"type": "rejection", "message": reason}


def finish(result: dict) -> dict:
    return {"type": "analysis", **result}
