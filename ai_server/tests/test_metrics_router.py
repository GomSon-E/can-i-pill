from fastapi.testclient import TestClient

from app.main import app
from app import metrics

client = TestClient(app)


def test_get_metrics_returns_summary_json():
    metrics._METRICS_BUFFER.clear()
    metrics.record_metric("/analyze", 200, 100.0, True)

    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data == metrics.get_metrics_summary()
