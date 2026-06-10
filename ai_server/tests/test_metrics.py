import json

from fastapi.testclient import TestClient
from google.genai import errors

from app import metrics
from app.main import app
from app.routers import ai


def test_record_metric_appends_to_buffer():
    metrics._METRICS_BUFFER.clear()

    metrics.record_metric("/analyze", 200, 123.4, True)

    assert len(metrics._METRICS_BUFFER) == 1
    entry = metrics._METRICS_BUFFER[0]
    assert entry["endpoint"] == "/analyze"
    assert entry["status_code"] == 200
    assert entry["latency_ms"] == 123.4
    assert entry["success"] is True


def test_get_metrics_summary_aggregates_by_endpoint():
    metrics._METRICS_BUFFER.clear()

    metrics.record_metric("/analyze", 200, 100.0, True)
    metrics.record_metric("/analyze", 200, 200.0, True)
    metrics.record_metric("/analyze", 500, 300.0, False)
    metrics.record_metric("/ocr", 200, 50.0, True)

    summary = metrics.get_metrics_summary()

    analyze = summary["endpoints"]["/analyze"]
    assert analyze["total"] == 3
    assert analyze["success"] == 2
    assert analyze["failure"] == 1
    assert analyze["status_codes"] == {"200": 2, "500": 1}
    assert analyze["avg_latency_ms"] == 200.0
    assert analyze["min_latency_ms"] == 100.0
    assert analyze["max_latency_ms"] == 300.0
    assert analyze["throughput_per_min"] == 3

    ocr = summary["endpoints"]["/ocr"]
    assert ocr["total"] == 1
    assert ocr["throughput_per_min"] == 1


class _FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)


def test_analyze_success_records_metric(monkeypatch):
    metrics._METRICS_BUFFER.clear()

    def fake_generate_content(*args, **kwargs):
        return _FakeResponse({
            "level": "safe",
            "doctorOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "pharmacistOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "alternatives": [],
        })

    monkeypatch.setattr(ai._client.models, "generate_content", fake_generate_content)

    client = TestClient(app)
    response = client.post("/analyze", json={"question": "질문", "context": ""})

    assert response.status_code == 200
    assert len(metrics._METRICS_BUFFER) == 1
    entry = metrics._METRICS_BUFFER[0]
    assert entry["endpoint"] == "/analyze"
    assert entry["status_code"] == 200
    assert entry["success"] is True


def test_analyze_failure_records_metric_with_api_error_code(monkeypatch):
    metrics._METRICS_BUFFER.clear()

    def fake_generate_content(*args, **kwargs):
        raise errors.APIError(503, {"error": {"message": "unavailable", "status": "UNAVAILABLE"}})

    monkeypatch.setattr(ai._client.models, "generate_content", fake_generate_content)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/analyze", json={"question": "질문", "context": ""})

    assert response.status_code == 500
    assert len(metrics._METRICS_BUFFER) == 3
    for entry in metrics._METRICS_BUFFER:
        assert entry["endpoint"] == "/analyze"
        assert entry["status_code"] == 503
        assert entry["success"] is False
