from fastapi.testclient import TestClient
from app.main import app

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
