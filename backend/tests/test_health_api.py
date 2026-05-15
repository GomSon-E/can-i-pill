from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


def setup_function():
    store_module.store["health"] = None


def test_post_health_creates_health():
    response = client.post("/health-info", json={
        "conditions": ["당뇨", "고혈압"],
        "allergies": ["페니실린"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["conditions"] == ["당뇨", "고혈압"]
    assert data["allergies"] == ["페니실린"]


def test_get_health_returns_health():
    client.post("/health-info", json={
        "conditions": ["당뇨"],
        "allergies": []
    })
    response = client.get("/health-info")
    assert response.status_code == 200
    assert response.json()["conditions"] == ["당뇨"]


def test_get_health_returns_404_when_no_health():
    response = client.get("/health-info")
    assert response.status_code == 404
