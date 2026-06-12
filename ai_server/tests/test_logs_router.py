from fastapi.testclient import TestClient

from app import analyze_logs, metrics
from app.main import app

client = TestClient(app)


def test_get_logs_requests_returns_recent_requests(monkeypatch, tmp_path):
    metrics._METRICS_BUFFER.clear()
    monkeypatch.setenv("AI_METRICS_CSV_PATH", str(tmp_path / "metrics.csv"))
    metrics.record_metric("/ocr", 200, 100.0, True)
    metrics.record_metric("/analyze", 200, 200.0, True)

    response = client.get("/logs/requests")

    assert response.status_code == 200
    data = response.json()
    assert len(data["requests"]) == 2
    assert data["requests"][0]["endpoint"] == "/analyze"


def test_get_logs_requests_respects_limit(monkeypatch, tmp_path):
    metrics._METRICS_BUFFER.clear()
    monkeypatch.setenv("AI_METRICS_CSV_PATH", str(tmp_path / "metrics.csv"))
    metrics.record_metric("/ocr", 200, 100.0, True)
    metrics.record_metric("/analyze", 200, 200.0, True)

    response = client.get("/logs/requests", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["requests"]) == 1


def test_get_logs_analyze_returns_recent_logs(monkeypatch, tmp_path):
    analyze_logs._LOG_BUFFER.clear()
    monkeypatch.setenv("AI_ANALYZE_LOGS_PATH", str(tmp_path / "analyze_logs.jsonl"))
    result = {"type": "analysis", "level": "safe", "trace": []}
    analyze_logs.record_analyze_log("질문", "컨텍스트", result, 123.4)

    response = client.get("/logs/analyze")

    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1
    assert data["logs"][0]["question"] == "질문"


def test_get_logs_analyze_respects_limit(monkeypatch, tmp_path):
    analyze_logs._LOG_BUFFER.clear()
    monkeypatch.setenv("AI_ANALYZE_LOGS_PATH", str(tmp_path / "analyze_logs.jsonl"))
    result = {"type": "analysis", "level": "safe", "trace": []}
    analyze_logs.record_analyze_log("첫번째", "", result, 1.0)
    analyze_logs.record_analyze_log("두번째", "", result, 2.0)

    response = client.get("/logs/analyze", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["logs"]) == 1
    assert response.json()["logs"][0]["question"] == "두번째"
