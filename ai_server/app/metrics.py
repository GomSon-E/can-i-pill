import csv
import os
import threading
import time

MAX_METRICS_BUFFER_SIZE = 1000
CSV_FIELDS = ["timestamp", "endpoint", "status_code", "latency_ms", "success"]

_METRICS_BUFFER = []
_CSV_LOCK = threading.Lock()


def _metrics_csv_path() -> str:
    return os.getenv("AI_METRICS_CSV_PATH", os.path.join(os.getcwd(), "data", "metrics.csv"))


def _ensure_metrics_csv(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def _append_metric_to_csv(entry: dict) -> None:
    path = _metrics_csv_path()
    with _CSV_LOCK:
        _ensure_metrics_csv(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writerow({
                "timestamp": entry["timestamp"],
                "endpoint": entry["endpoint"],
                "status_code": entry["status_code"],
                "latency_ms": entry["latency_ms"],
                "success": entry["success"],
            })


def _load_metrics_from_csv() -> list[dict]:
    path = _metrics_csv_path()
    if not os.path.exists(path):
        return list(_METRICS_BUFFER)

    entries = []
    with _CSV_LOCK:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    entries.append({
                        "timestamp": float(row["timestamp"]),
                        "endpoint": row["endpoint"],
                        "status_code": int(row["status_code"]),
                        "latency_ms": float(row["latency_ms"]),
                        "success": row["success"] == "True",
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    return entries


def record_metric(endpoint: str, status_code: int, latency_ms: float, success: bool) -> None:
    entry = {
        "endpoint": endpoint,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "success": success,
        "timestamp": time.time(),
    }
    _METRICS_BUFFER.append(entry)
    if len(_METRICS_BUFFER) > MAX_METRICS_BUFFER_SIZE:
        del _METRICS_BUFFER[: len(_METRICS_BUFFER) - MAX_METRICS_BUFFER_SIZE]
    _append_metric_to_csv(entry)


def get_metrics_summary() -> dict:
    now = time.time()
    endpoints = {}

    for entry in _load_metrics_from_csv():
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


def get_recent_requests(limit: int = 50) -> list[dict]:
    entries = _load_metrics_from_csv()
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries[:limit]
