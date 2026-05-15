from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


def setup_function():
    store_module.store["user"] = None


def test_post_user_creates_user():
    response = client.post("/user", json={
        "nickname": "영자",
        "year": "1961",
        "month": "3",
        "day": "12",
        "gender": "여성"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "영자"
    assert data["year"] == "1961"
    assert data["month"] == "3"
    assert data["day"] == "12"
    assert data["gender"] == "여성"
    assert data["last_prescription_check"] is None


def test_get_user_returns_user():
    client.post("/user", json={
        "nickname": "영자",
        "year": "1961",
        "month": "3",
        "day": "12",
        "gender": "여성"
    })
    response = client.get("/user")
    assert response.status_code == 200
    assert response.json()["nickname"] == "영자"


def test_get_user_returns_404_when_no_user():
    response = client.get("/user")
    assert response.status_code == 404


def test_put_user_updates_user():
    client.post("/user", json={
        "nickname": "영자",
        "year": "1961",
        "month": "3",
        "day": "12",
        "gender": "여성"
    })
    response = client.put("/user", json={
        "nickname": "영자할머니",
        "last_prescription_check": "2026-05-16"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "영자할머니"
    assert data["last_prescription_check"] == "2026-05-16"
