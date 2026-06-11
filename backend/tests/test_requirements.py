import os


def test_requirements_txt_exists():
    req_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    assert os.path.exists(req_path), "backend/requirements.txt 가 없습니다"


def test_requirements_contains_core_packages():
    req_path = os.path.join(os.path.dirname(__file__), "../requirements.txt")
    with open(req_path) as f:
        content = f.read()

    assert "fastapi" in content
    assert "uvicorn" in content
    assert "httpx" in content
    assert "python-multipart" in content
