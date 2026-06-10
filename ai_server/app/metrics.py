import time

MAX_METRICS_BUFFER_SIZE = 1000

_METRICS_BUFFER = []


def record_metric(endpoint: str, status_code: int, latency_ms: float, success: bool) -> None:
    _METRICS_BUFFER.append({
        "endpoint": endpoint,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "success": success,
        "timestamp": time.time(),
    })
    if len(_METRICS_BUFFER) > MAX_METRICS_BUFFER_SIZE:
        del _METRICS_BUFFER[: len(_METRICS_BUFFER) - MAX_METRICS_BUFFER_SIZE]


def get_metrics_summary() -> dict:
    now = time.time()
    endpoints = {}

    for entry in _METRICS_BUFFER:
        endpoint = entry["endpoint"]
        stats = endpoints.setdefault(endpoint, {
            "total": 0,
            "success": 0,
            "failure": 0,
            "status_codes": {},
            "_latencies": [],
            "throughput_per_min": 0,
        })

        stats["total"] += 1
        if entry["success"]:
            stats["success"] += 1
        else:
            stats["failure"] += 1

        status_key = str(entry["status_code"])
        stats["status_codes"][status_key] = stats["status_codes"].get(status_key, 0) + 1

        stats["_latencies"].append(entry["latency_ms"])

        if now - entry["timestamp"] <= 60:
            stats["throughput_per_min"] += 1

    for stats in endpoints.values():
        latencies = stats.pop("_latencies")
        stats["avg_latency_ms"] = sum(latencies) / len(latencies)
        stats["min_latency_ms"] = min(latencies)
        stats["max_latency_ms"] = max(latencies)

    return {"endpoints": endpoints}
