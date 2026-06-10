import json

from fastapi.testclient import TestClient

from app.main import app
from app import concurrency
from app.routers import ai

client = TestClient(app)


class _FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)


def test_ocr_acquires_gemini_semaphore(monkeypatch):
    seen_values = []

    def fake_generate_content(*args, **kwargs):
        seen_values.append(concurrency.GEMINI_SEMAPHORE._value)
        return _FakeResponse({"name": "병원", "drugs": []})

    monkeypatch.setattr(ai._client.models, "generate_content", fake_generate_content)

    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/ocr", files={"image": f})

    assert response.status_code == 200
    assert seen_values == [concurrency.MAX_CONCURRENT_GEMINI_CALLS - 1]


def test_label_acquires_gemini_semaphore(monkeypatch):
    seen_values = []

    def fake_generate_content(*args, **kwargs):
        seen_values.append(concurrency.GEMINI_SEMAPHORE._value)
        return _FakeResponse({"name": "영양제", "nutrients": []})

    monkeypatch.setattr(ai._client.models, "generate_content", fake_generate_content)

    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/label", files={"image": f})

    assert response.status_code == 200
    assert seen_values == [concurrency.MAX_CONCURRENT_GEMINI_CALLS - 1]


def test_analyze_acquires_gemini_semaphore(monkeypatch):
    seen_values = []

    def fake_run_agent(question, extra_context=""):
        seen_values.append(concurrency.GEMINI_SEMAPHORE._value)
        return {
            "type": "analysis",
            "level": "safe",
            "doctorOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "pharmacistOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "alternatives": [],
            "trace": [],
        }

    monkeypatch.setattr(ai.harness, "run_agent", fake_run_agent)

    response = client.post("/analyze", json={"question": "질문", "context": ""})

    assert response.status_code == 200
    assert seen_values == [concurrency.MAX_CONCURRENT_GEMINI_CALLS - 1]
