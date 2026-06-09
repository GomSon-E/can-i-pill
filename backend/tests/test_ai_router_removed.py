import os


def test_backend_ai_router_file_does_not_exist():
    ai_router_path = os.path.join(os.path.dirname(__file__), "../app/routers/ai.py")
    assert not os.path.exists(ai_router_path), "backend/app/routers/ai.py 가 아직 존재합니다 — 삭제해야 합니다"
