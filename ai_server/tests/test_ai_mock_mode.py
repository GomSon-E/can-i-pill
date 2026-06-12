from fastapi.testclient import TestClient
from app.main import app
from app.mock_responses import MOCK_OCR_RESPONSE, MOCK_LABEL_RESPONSE, MOCK_ANALYZE_RESPONSE

client = TestClient(app)


def test_mock_ocr_response_has_expected_shape():
    assert MOCK_OCR_RESPONSE["name"] == "Mock 처방전"
    assert MOCK_OCR_RESPONSE["drugs"][0]["name"] == "메트포르민"


def test_mock_label_response_has_expected_shape():
    assert MOCK_LABEL_RESPONSE["name"] == "Mock 영양제"
    assert MOCK_LABEL_RESPONSE["nutrients"][0]["ingredient"] == "비타민C"


def test_mock_analyze_response_has_expected_shape():
    assert MOCK_ANALYZE_RESPONSE["level"] == "caution"
    assert MOCK_ANALYZE_RESPONSE["doctorOpinion"]["summary"] == "Mock 의사 의견"


from app.routers import ai as ai_router


def test_ai_mock_mode_flag_is_enabled():
    assert ai_router.AI_MOCK_MODE is True


def test_client_is_none_in_mock_mode():
    assert ai_router._client is None


def test_ocr_returns_mock_response_in_mock_mode():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/ocr", files={"image": f})
    assert response.status_code == 200
    assert response.json() == MOCK_OCR_RESPONSE


def test_label_returns_mock_response_in_mock_mode():
    with open("tests/dummy_image.png", "rb") as f:
        response = client.post("/label", files={"image": f})
    assert response.status_code == 200
    assert response.json() == MOCK_LABEL_RESPONSE
