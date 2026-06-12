import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from app.main import app

client = TestClient(app)

AI_SERVER_URL = "http://localhost:8001"


def make_httpx_response(json_data: dict, status_code: int = 200):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.content = b"{}"
    response.headers = {"content-type": "application/json"}
    return response


def make_httpx_html_response(html: str, status_code: int = 200):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.content = html.encode()
    response.headers = {"content-type": "text/html"}
    return response


def patched_get_client(mock_response):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client


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

    def test_ocr_returns_502_when_ai_server_unreachable(self):
        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("name resolution failed"))
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/ocr",
                files={"image": ("test.jpg", b"fake image bytes", "image/jpeg")},
            )

        assert response.status_code == 502
        assert "AI server connection failed" in response.json()["detail"]


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

    def test_analyze_proxy_uses_extended_timeout(self):
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

            client.post(
                "/analyze",
                json={"question": "아스피린과 커피", "context": ""},
            )

        _, kwargs = mock_client_cls.call_args
        assert kwargs["timeout"] == pytest.approx(120.0)


class TestDashboardProxy:
    def test_dashboard_proxy_forwards_to_ai_server(self):
        mock_response = make_httpx_html_response("<html><body>대시보드</body></html>")

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = patched_get_client(mock_response)

            response = client.get("/dashboard")

        assert response.status_code == 200
        assert "대시보드" in response.text

    def test_dashboard_returns_502_when_ai_server_unreachable(self):
        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("name resolution failed"))
            mock_client_cls.return_value = mock_client

            response = client.get("/dashboard")

        assert response.status_code == 502


class TestMetricsProxy:
    def test_metrics_proxy_forwards_to_ai_server(self):
        expected = {"endpoints": {"/ocr": {"total": 10, "success": 9, "failure": 1}}}
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = patched_get_client(mock_response)

            response = client.get("/metrics")

        assert response.status_code == 200
        assert response.json() == expected


class TestLogsProxy:
    def test_logs_requests_proxy_forwards_to_ai_server(self):
        expected = {"requests": [{"endpoint": "/ocr", "status": "success"}]}
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = patched_get_client(mock_response)

            response = client.get("/logs/requests")

        assert response.status_code == 200
        assert response.json() == expected

    def test_logs_requests_proxy_forwards_limit_query_param(self):
        mock_response = make_httpx_response({"requests": []})

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = patched_get_client(mock_response)
            mock_client_cls.return_value = mock_client

            client.get("/logs/requests?limit=10")

        _, kwargs = mock_client.get.call_args
        assert kwargs["params"] == {"limit": 10}

    def test_logs_analyze_proxy_forwards_to_ai_server(self):
        expected = {"logs": [{"question": "아스피린과 커피"}]}
        mock_response = make_httpx_response(expected)

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = patched_get_client(mock_response)

            response = client.get("/logs/analyze")

        assert response.status_code == 200
        assert response.json() == expected

    def test_logs_analyze_proxy_forwards_limit_query_param(self):
        mock_response = make_httpx_response({"logs": []})

        with patch("app.routers.ai_proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = patched_get_client(mock_response)
            mock_client_cls.return_value = mock_client

            client.get("/logs/analyze?limit=5")

        _, kwargs = mock_client.get.call_args
        assert kwargs["params"] == {"limit": 5}
