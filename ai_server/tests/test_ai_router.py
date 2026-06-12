import logging

from fastapi.testclient import TestClient
from app.main import app
from app.harness import harness

client = TestClient(app)


def test_post_ocr_without_image_returns_422():
    response = client.post("/ocr")
    assert response.status_code == 422


def test_post_label_without_image_returns_422():
    response = client.post("/label")
    assert response.status_code == 422


def test_post_analyze_without_body_returns_422():
    response = client.post("/analyze")
    assert response.status_code == 422


def test_post_analyze_logs_result(monkeypatch, caplog):
    fake_result = {
        "type": "analysis",
        "level": "safe",
        "doctorOpinion": {"summary": "요약", "detail": "상세"},
        "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
        "alternatives": [],
        "trace": [{"action": "validate_query", "args": {}, "observation": {}}],
    }
    monkeypatch.setattr(harness, "run_agent", lambda question, context: fake_result)

    with caplog.at_level(logging.INFO):
        response = client.post("/analyze", json={"question": "홍삼 먹어도 되나요?", "context": ""})

    assert response.status_code == 200
    assert any("analysis" in record.message and "safe" in record.message for record in caplog.records)
