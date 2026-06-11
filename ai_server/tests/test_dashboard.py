from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_dashboard_returns_html():
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_get_dashboard_includes_tabs():
    response = client.get("/dashboard")

    html = response.text
    assert "통계" in html
    assert "최근 요청" in html
    assert "로그" in html
