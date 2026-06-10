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


def _generate_analysis(question: str, context: str) -> dict:
    from app.routers.ai import MODEL, _client

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
    from app.routers.ai import MODEL, _client

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
