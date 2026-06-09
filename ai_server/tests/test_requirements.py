import os


def test_requirements_txt_exists():
    req_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    assert os.path.exists(req_path), "ai_server/requirements.txt 가 없습니다"


def test_requirements_contains_core_packages():
    req_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    content = open(req_path).read()
    assert "google-genai" in content
    assert "fastapi" in content
    assert "uvicorn" in content
