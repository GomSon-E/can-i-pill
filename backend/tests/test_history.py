from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


HISTORY_PAYLOAD = {
    "level": "safe",
    "question": "메트포르민과 비타민C를 같이 먹어도 될까요?",
    "doctorOpinion": {
        "summary": "현재 복용 중인 약과 상호작용이 없습니다.",
        "detail": "권장량을 지키면 큰 문제는 알려져 있지 않습니다.",
    },
    "pharmacistOpinion": {
        "summary": "시간 간격 조절 없이 복용 가능합니다.",
        "detail": "불편감이 있으면 복용을 멈추고 상담하세요.",
    },
    "alternatives": [],
}


def setup_function():
    store_module.store["history"] = []


def test_get_history_returns_empty_list():
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == {"history": []}


def test_post_history_creates_item():
    response = client.post("/history", json=HISTORY_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["level"] == "safe"
    assert data["question"] == "메트포르민과 비타민C를 같이 먹어도 될까요?"
    assert data["doctorOpinion"]["summary"] == "현재 복용 중인 약과 상호작용이 없습니다."
    assert data["pharmacistOpinion"]["summary"] == "시간 간격 조절 없이 복용 가능합니다."
    assert data["alternatives"] == []
    assert "created_at" in data


def test_get_history_returns_all_newest_first():
    client.post("/history", json={**HISTORY_PAYLOAD, "question": "첫번째 질문"})
    client.post("/history", json={**HISTORY_PAYLOAD, "level": "caution", "question": "두번째 질문"})

    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()["history"]
    assert len(history) == 2
    # Newest first
    assert history[0]["question"] == "두번째 질문"
    assert history[1]["question"] == "첫번째 질문"


def test_get_history_item_by_id():
    post_resp = client.post("/history", json={**HISTORY_PAYLOAD, "question": "질문"})
    history_id = post_resp.json()["id"]

    response = client.get(f"/history/{history_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == history_id
    assert data["question"] == "질문"


def test_post_history_stores_multi_item_analysis_without_top_level_opinions():
    payload = {
        "level": "danger",
        "question": "홍삼이랑 비타민C 같이 먹어도 되나요?",
        "items": [
            {
                "name": "홍삼",
                "level": "caution",
                "doctorOpinion": {
                    "summary": "혈압약과 상호작용 가능성",
                    "detail": "혈압약 효과가 줄어들 수 있습니다.",
                },
                "pharmacistOpinion": {
                    "summary": "복용 시간 조절 필요",
                    "detail": "복용 시간을 2시간 띄우세요.",
                },
                "alternatives": [],
            },
            {
                "name": "비타민C",
                "level": "danger",
                "doctorOpinion": {
                    "summary": "출혈 위험 증가",
                    "detail": "출혈 위험이 커질 수 있습니다.",
                },
                "pharmacistOpinion": {
                    "summary": "즉시 상담 필요",
                    "detail": "복용 간격을 두고 의사와 상담하세요.",
                },
                "alternatives": [],
            },
        ],
    }

    post_resp = client.post("/history", json=payload)

    assert post_resp.status_code == 200
    history_id = post_resp.json()["id"]
    response = client.get(f"/history/{history_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == payload["items"]
    assert data["level"] == "danger"


def test_get_history_item_returns_404_when_not_found():
    response = client.get("/history/nonexistent-id")
    assert response.status_code == 404
