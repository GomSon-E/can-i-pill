from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_post_ocr_returns_mock_prescription():
    response = client.post("/ocr")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "drugs" in data
    assert isinstance(data["drugs"], list)
    assert len(data["drugs"]) > 0
    assert "name" in data["drugs"][0]
    assert "purpose" in data["drugs"][0]


def test_post_label_returns_mock_supplement():
    response = client.post("/label")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "ingredients" in data
    assert isinstance(data["ingredients"], list)


def test_post_analyze_returns_mock_analysis():
    response = client.post("/analyze", json={
        "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
        "context": "당뇨 환자, 메트포르민 복용 중"
    })
    assert response.status_code == 200
    data = response.json()
    assert "level" in data
    assert "summary" in data
    assert "alternatives" in data
    assert "detail" in data
    assert data["level"] in ["safe", "warning", "danger"]


def test_post_analyze_reflects_question():
    question = "이 약 먹어도 되나요?"
    response = client.post("/analyze", json={
        "question": question,
        "context": "테스트 컨텍스트"
    })
    assert response.status_code == 200
    # The response should be meaningful
    data = response.json()
    assert len(data["summary"]) > 0
