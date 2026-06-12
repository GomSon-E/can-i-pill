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
