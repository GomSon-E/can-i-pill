from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


def setup_function():
    store_module.store["prescriptions"] = []


def test_get_prescriptions_returns_empty_list():
    response = client.get("/prescriptions")
    assert response.status_code == 200
    assert response.json() == {"prescriptions": []}


def test_post_prescription_creates_prescription():
    response = client.post("/prescriptions", json={
        "name": "내과 처방전",
        "drugs": [{"name": "메트포르민"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "내과 처방전"
    assert data["drugs"][0]["name"] == "메트포르민"


def test_get_prescriptions_returns_all():
    client.post("/prescriptions", json={
        "name": "내과 처방전",
        "drugs": [{"name": "메트포르민"}]
    })
    client.post("/prescriptions", json={
        "name": "외과 처방전",
        "drugs": [{"name": "아스피린"}]
    })
    response = client.get("/prescriptions")
    assert response.status_code == 200
    assert len(response.json()["prescriptions"]) == 2


def test_put_prescription_updates_prescription():
    post_resp = client.post("/prescriptions", json={
        "name": "내과 처방전",
        "drugs": [{"name": "메트포르민"}]
    })
    prescription_id = post_resp.json()["id"]

    response = client.put(f"/prescriptions/{prescription_id}", json={
        "name": "수정된 처방전",
        "drugs": [{"name": "아스피린"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prescription_id
    assert data["name"] == "수정된 처방전"
    assert data["drugs"][0]["name"] == "아스피린"


def test_put_prescription_returns_404_when_not_found():
    response = client.put("/prescriptions/nonexistent-id", json={
        "name": "처방전",
        "drugs": []
    })
    assert response.status_code == 404


def test_delete_prescription_removes_prescription():
    post_resp = client.post("/prescriptions", json={
        "name": "내과 처방전",
        "drugs": [{"name": "메트포르민"}]
    })
    prescription_id = post_resp.json()["id"]

    response = client.delete(f"/prescriptions/{prescription_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    get_resp = client.get("/prescriptions")
    assert len(get_resp.json()["prescriptions"]) == 0


def test_delete_prescription_returns_404_when_not_found():
    response = client.delete("/prescriptions/nonexistent-id")
    assert response.status_code == 404
