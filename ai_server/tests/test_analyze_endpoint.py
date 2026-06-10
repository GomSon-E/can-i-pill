import importlib

from fastapi.testclient import TestClient

from app.main import app
from app.routers import ai


client = TestClient(app)


def test_analyze_request_schema_keeps_question_and_context_fields():
    request = ai.AnalyzeRequest(question="홍삼 먹어도 되나요?")

    assert request.question == "홍삼 먹어도 되나요?"
    assert request.context == ""


def test_post_analyze_returns_rejection_for_irrelevant_question(monkeypatch):
    harness = importlib.import_module("app.harness.harness")

    def fake_run_agent(question, extra_context=""):
        return {
            "type": "rejection",
            "message": "이 질문은 약물·영양제·음식 상호작용 분석 서비스의 범위를 벗어났습니다.",
            "trace": [],
        }

    monkeypatch.setattr(ai.harness, "run_agent", fake_run_agent)

    response = client.post("/analyze", json={"question": "오늘 날씨 어때?"})

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "rejection"


def test_post_analyze_returns_clarification_for_unclear_question(monkeypatch):
    def fake_run_agent(question, extra_context=""):
        return {"clarification_prompt": "섭취하려는 항목을 알려주세요.", "trace": []}

    monkeypatch.setattr(ai.harness, "run_agent", fake_run_agent)

    response = client.post("/analyze", json={"question": "이거 먹어도 돼요?"})

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "clarification"
    assert data["clarification_prompt"] == "섭취하려는 항목을 알려주세요."


def test_post_analyze_returns_analysis_for_clear_question(monkeypatch):
    def fake_run_agent(question, extra_context=""):
        return {
            "type": "analysis",
            "level": "safe",
            "doctorOpinion": {"summary": "요약", "detail": "상세"},
            "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
            "alternatives": [],
            "trace": [],
        }

    monkeypatch.setattr(ai.harness, "run_agent", fake_run_agent)

    response = client.post("/analyze", json={"question": "홍삼 먹어도 되나요?"})

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "analysis"
    assert data["level"] == "safe"
    assert "doctorOpinion" in data
