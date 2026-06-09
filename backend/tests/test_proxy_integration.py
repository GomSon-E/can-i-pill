"""
백엔드 → AI 서버 → 응답 체인 통합 테스트.

실제 포트(8000/8001) 없이 두 ASGI 앱을 httpx.ASGITransport로 직접 연결.
"""
import pytest
import httpx
from fastapi import FastAPI, File, UploadFile
from fastapi.testclient import TestClient
from pydantic import BaseModel


class _AnalyzeRequest(BaseModel):
    question: str
    context: str = ""


def _make_fake_ai_server() -> FastAPI:
    ai = FastAPI()

    @ai.post("/ocr")
    async def ocr(image: UploadFile = File(...)):
        return {
            "name": "통합테스트 처방전",
            "drugs": [{"name": "아스피린", "dosage": "100mg", "frequency": "1일 1회", "days": 30, "usage": "식후", "cautions": ""}],
        }

    @ai.post("/label")
    async def label(image: UploadFile = File(...)):
        return {"name": "통합테스트 영양제", "nutrients": [{"ingredient": "비타민C", "amount": "500", "unit": "mg"}]}

    @ai.post("/analyze")
    async def analyze(body: _AnalyzeRequest):
        return {
            "level": "safe",
            "doctorOpinion": {"summary": "안전합니다", "detail": "문제 없습니다."},
            "pharmacistOpinion": {"summary": "복용 가능합니다", "detail": "안심하세요."},
            "alternatives": [],
        }

    return ai


class TestProxyIntegration:
    """백엔드 프록시 → AI 서버 체인 통합 테스트."""

    @pytest.fixture(autouse=True)
    def patch_ai_client(self, monkeypatch):
        fake_ai = _make_fake_ai_server()
        transport = httpx.ASGITransport(app=fake_ai)

        import app.routers.ai_proxy as proxy_mod

        original_make = proxy_mod._make_client

        def fake_make(**kwargs):
            return httpx.AsyncClient(transport=transport, base_url="http://ai-server:8001", **kwargs)

        monkeypatch.setattr(proxy_mod, "_make_client", fake_make)
        yield
        monkeypatch.setattr(proxy_mod, "_make_client", original_make)

    def test_analyze_chain_returns_safe(self):
        from app.main import app
        client = TestClient(app)
        response = client.post("/analyze", json={"question": "아스피린과 커피", "context": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "safe"
        assert "doctorOpinion" in data
        assert "pharmacistOpinion" in data

    def test_ocr_chain_returns_prescription(self):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/ocr",
            files={"image": ("test.jpg", b"fake", "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "통합테스트 처방전"
        assert len(data["drugs"]) > 0

    def test_label_chain_returns_supplement(self):
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/label",
            files={"image": ("label.jpg", b"fake", "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "통합테스트 영양제"
        assert len(data["nutrients"]) > 0

    def test_analyze_missing_question_returns_422(self):
        from app.main import app
        client = TestClient(app)
        response = client.post("/analyze", json={})
        assert response.status_code == 422
