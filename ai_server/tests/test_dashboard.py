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


def test_get_dashboard_does_not_auto_refresh():
    response = client.get("/dashboard")

    assert "setInterval" not in response.text


def test_get_dashboard_includes_pagination_controls():
    response = client.get("/dashboard")

    html = response.text
    assert "requests-prev" in html
    assert "requests-next" in html
    assert "logs-prev" in html
    assert "logs-next" in html
    assert "/logs/requests?limit=${pageSize}&offset=${pagination.requests.offset}" in html
    assert "/logs/analyze?limit=${pageSize}&offset=${pagination.logs.offset}" in html
