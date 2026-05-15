from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


def setup_function():
    store_module.store["history"] = []


def test_get_history_returns_empty_list():
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == {"history": []}


def test_post_history_creates_item():
    response = client.post("/history", json={
        "level": "safe",
        "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
        "summary": "현재 복용 중인 약과 상호작용이 없습니다."
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["level"] == "safe"
    assert data["question"] == "메트포르민과 비타민C를 같이 먹어도 될까요?"
    assert data["summary"] == "현재 복용 중인 약과 상호작용이 없습니다."
    assert "created_at" in data


def test_get_history_returns_all_newest_first():
    client.post("/history", json={"level": "safe", "question": "첫번째 질문", "summary": "요약1"})
    client.post("/history", json={"level": "warning", "question": "두번째 질문", "summary": "요약2"})

    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()["history"]
    assert len(history) == 2
    # Newest first
    assert history[0]["question"] == "두번째 질문"
    assert history[1]["question"] == "첫번째 질문"


def test_get_history_item_by_id():
    post_resp = client.post("/history", json={
        "level": "safe",
        "question": "질문",
        "summary": "요약"
    })
    history_id = post_resp.json()["id"]

    response = client.get(f"/history/{history_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == history_id
    assert data["question"] == "질문"


def test_get_history_item_returns_404_when_not_found():
    response = client.get("/history/nonexistent-id")
    assert response.status_code == 404
