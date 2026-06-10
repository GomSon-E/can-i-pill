from fastapi.testclient import TestClient
from app.main import app
import app.store as store_module

client = TestClient(app)


def setup_function():
    store_module.store["supplements"] = []


def test_get_supplements_returns_empty_list():
    response = client.get("/supplements")
    assert response.status_code == 200
    assert response.json() == {"supplements": []}


def test_post_supplement_creates_supplement():
    response = client.post("/supplements", json={
        "supplements": [{
            "name": "비타민C",
            "ingredients": ["아스코르브산"],
        }]
    })
    assert response.status_code == 200
    data = response.json()
    assert "supplements" in data
    assert len(data["supplements"]) == 1
    supplement = data["supplements"][0]
    assert "id" in supplement
    assert supplement["name"] == "비타민C"
    assert supplement["ingredients"] == ["아스코르브산"]


def test_get_supplements_returns_all():
    client.post("/supplements", json={
        "supplements": [
            {"name": "비타민C", "ingredients": ["아스코르브산"]},
            {"name": "오메가3", "ingredients": ["EPA", "DHA"]},
        ]
    })
    response = client.get("/supplements")
    assert response.status_code == 200
    assert len(response.json()["supplements"]) == 2


def test_delete_supplement_removes_supplement():
    post_resp = client.post("/supplements", json={
        "supplements": [{
            "name": "비타민C",
            "ingredients": ["아스코르브산"],
        }]
    })
    supplement_id = post_resp.json()["supplements"][0]["id"]

    response = client.delete(f"/supplements/{supplement_id}")
    assert response.status_code == 200
    assert response.json()["supplements"] == []


def test_delete_supplement_returns_404_when_not_found():
    response = client.delete("/supplements/nonexistent-id")
    assert response.status_code == 404
