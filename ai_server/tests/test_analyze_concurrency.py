import asyncio
import time

import httpx

from app.main import app
from app.routers import ai


def test_analyze_requests_run_concurrently_not_serially(monkeypatch):
    def fake_run_agent(question, extra_context=""):
        time.sleep(0.2)
        return {
            "type": "analysis",
            "level": "safe",
            "doctorOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "pharmacistOpinion": {"summary": "괜찮아요", "detail": "괜찮아요"},
            "alternatives": [],
            "trace": [],
        }

    monkeypatch.setattr(ai.harness, "run_agent", fake_run_agent)
    monkeypatch.setattr(ai, "record_metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai, "record_analyze_log", lambda *args, **kwargs: None)

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            start = time.monotonic()
            responses = await asyncio.gather(*(
                client.post("/analyze", json={"question": "질문", "context": ""})
                for _ in range(10)
            ))
            elapsed = time.monotonic() - start
            return responses, elapsed

    responses, elapsed = asyncio.run(run())

    assert all(r.status_code == 200 for r in responses)
    # 직렬 처리라면 10 * 0.2초 = 2.0초 이상 걸린다.
    # event loop를 막지 않고 동시에 처리되면 0.2~0.5초대에 끝나야 한다.
    assert elapsed < 1.0
