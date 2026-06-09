import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from app.main import app

client = TestClient(app)

AI_SERVER_URL = "http://ai-server:8001"


def make_httpx_response(json_data: dict, status_code: int = 200):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.content = b"{}"
    response.headers = {"content-type": "application/json"}
    return response


class TestOcrProxy:
    def test_ocr_proxy_forwards_to_ai_server(self):
        mock_response = make_httpx_response({"name": "처방전", "drugs": []})

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            dummy_image = b"fake image bytes"
            response = client.post(
                "/ocr",
                files={"image": ("test.jpg", dummy_image, "image/jpeg")},
            )

        assert response.status_code == 200

    def test_ocr_proxy_returns_ai_server_response(self):
        expected = {"name": "내과 처방전", "drugs": [{"name": "아스피린"}]}
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            dummy_image = b"fake image bytes"
            response = client.post(
                "/ocr",
                files={"image": ("test.jpg", dummy_image, "image/jpeg")},
            )

        assert response.json() == expected

    def test_ocr_no_image_returns_422(self):
        response = client.post("/ocr")
        assert response.status_code == 422


class TestLabelProxy:
    def test_label_proxy_forwards_to_ai_server(self):
        mock_response = make_httpx_response({"name": "비타민C", "nutrients": []})

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            dummy_image = b"fake label bytes"
            response = client.post(
                "/label",
                files={"image": ("label.jpg", dummy_image, "image/jpeg")},
            )

        assert response.status_code == 200

    def test_label_proxy_returns_ai_server_response(self):
        expected = {"name": "오메가3", "nutrients": [{"ingredient": "EPA", "amount": "500", "unit": "mg"}]}
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            dummy_image = b"fake label bytes"
            response = client.post(
                "/label",
                files={"image": ("label.jpg", dummy_image, "image/jpeg")},
            )

        assert response.json() == expected

    def test_label_no_image_returns_422(self):
        response = client.post("/label")
        assert response.status_code == 422


class TestAnalyzeProxy:
    def test_analyze_proxy_forwards_to_ai_server(self):
        mock_response = make_httpx_response({
            "level": "safe",
            "doctorOpinion": {"summary": "안전", "detail": ""},
            "pharmacistOpinion": {"summary": "안전", "detail": ""},
            "alternatives": [],
        })

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/analyze",
                json={"question": "아스피린과 커피", "context": ""},
            )

        assert response.status_code == 200

    def test_analyze_proxy_returns_ai_server_response(self):
        expected = {
            "level": "danger",
            "doctorOpinion": {"summary": "위험", "detail": "복용 중단"},
            "pharmacistOpinion": {"summary": "금지", "detail": ""},
            "alternatives": ["타이레놀"],
        }
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/analyze",
                json={"question": "위험한 조합", "context": ""},
            )

        assert response.json() == expected

    def test_analyze_missing_question_returns_422(self):
        response = client.post("/analyze", json={})
        assert response.status_code == 422
