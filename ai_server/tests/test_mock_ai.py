import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.harness import tools as harness_tools

client = TestClient(app)


@pytest.fixture(autouse=True)
def _registered_medication(monkeypatch):
    monkeypatch.setattr(
        harness_tools,
        "_fetch_backend_data",
        lambda: ([{"drugs": [{"name": "메트포르민"}]}], [], {}),
    )


def _assert_analysis_shape(entry):
    assert entry["level"] in ["safe", "caution", "danger"]
    assert isinstance(entry["doctorOpinion"], dict)
    assert isinstance(entry["pharmacistOpinion"], dict)
    assert "summary" in entry["doctorOpinion"]
    assert "detail" in entry["doctorOpinion"]
    assert "summary" in entry["pharmacistOpinion"]
    assert "detail" in entry["pharmacistOpinion"]
    assert isinstance(entry["alternatives"], list)


def test_post_ocr_without_image_returns_422():
    response = client.post("/ocr")
    assert response.status_code == 422


def test_post_ocr_returns_mock_prescription():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/ocr", files={"image": f})
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "drugs" in data
    assert isinstance(data["drugs"], list)
    assert len(data["drugs"]) > 0
    drug = data["drugs"][0]
    assert "name" in drug
    assert "dosage" in drug
    assert "frequency" in drug
    assert "days" in drug
    assert "usage" in drug
    assert "cautions" in drug


def test_post_ocr_returns_new_schema():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/ocr", files={"image": f})
    assert response.status_code == 200
    data = response.json()
    assert "drugs" in data
    assert isinstance(data["drugs"], list)
    assert len(data["drugs"]) > 0
    drug = data["drugs"][0]
    assert "name" in drug
    assert "dosage" in drug
    assert "frequency" in drug
    assert "days" in drug
    assert "usage" in drug
    assert "cautions" in drug


def test_post_label_without_image_returns_422():
    response = client.post("/label")
    assert response.status_code == 422


def test_post_label_returns_mock_supplement():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/label", files={"image": f})
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "nutrients" in data
    assert isinstance(data["nutrients"], list)
    assert len(data["nutrients"]) > 0


def test_post_label_returns_new_schema():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/label", files={"image": f})
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "nutrients" in data
    assert isinstance(data["nutrients"], list)
    assert len(data["nutrients"]) > 0
    nutrient = data["nutrients"][0]
    assert "ingredient" in nutrient
    assert "amount" in nutrient
    assert "unit" in nutrient


def test_post_analyze_returns_mock_analysis():
    response = client.post("/analyze", json={
        "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
        "context": "당뇨 환자, 메트포르민 복용 중"
    })
    assert response.status_code == 200
    data = response.json()
    assert "level" in data
    assert data["level"] in ["safe", "caution", "danger"]
    if "items" in data:
        for item in data["items"]:
            _assert_analysis_shape(item)
    else:
        _assert_analysis_shape(data)


def test_post_analyze_reflects_question():
    question = "메트포르민과 비타민C를 같이 먹어도 될까요?"
    response = client.post("/analyze", json={
        "question": question,
        "context": "당뇨 환자, 메트포르민 복용 중"
    })
    assert response.status_code == 200
    # The response should be meaningful
    data = response.json()
    if "items" in data:
        assert len(data["items"][0]["doctorOpinion"]["summary"]) > 0
    else:
        assert len(data["doctorOpinion"]["summary"]) > 0


def test_post_analyze_returns_new_schema():
    response = client.post("/analyze", json={
        "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
        "context": "당뇨 환자, 메트포르민 복용 중"
    })
    assert response.status_code == 200
    data = response.json()
    assert "level" in data
    assert data["level"] in ["safe", "caution", "danger"]
    if "items" in data:
        assert isinstance(data["items"], list)
        for item in data["items"]:
            assert "name" in item
            _assert_analysis_shape(item)
    else:
        _assert_analysis_shape(data)


def test_post_analyze_level_values_are_valid():
    for _ in range(3):
        response = client.post("/analyze", json={
            "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
            "context": "당뇨 환자, 메트포르민 복용 중"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["level"] in ["safe", "caution", "danger"]
