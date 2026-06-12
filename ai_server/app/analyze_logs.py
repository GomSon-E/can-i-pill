import json
import os
import threading
import time

MAX_LOG_BUFFER_SIZE = 200

_LOG_BUFFER = []
_LOG_LOCK = threading.Lock()


def _analyze_logs_path() -> str:
    return os.getenv("AI_ANALYZE_LOGS_PATH", os.path.join(os.getcwd(), "data", "analyze_logs.jsonl"))


def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _append_log_to_file(entry: dict) -> None:
    path = _analyze_logs_path()
    with _LOG_LOCK:
        _ensure_dir(path)
        with open(path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_logs_from_file() -> list[dict]:
    path = _analyze_logs_path()
    if not os.path.exists(path):
        return list(_LOG_BUFFER)

    entries = []
    with _LOG_LOCK:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def record_analyze_log(question: str, context: str, result: dict, latency_ms: float) -> None:
    entry = {
        "timestamp": time.time(),
        "question": question,
        "context": context,
        "type": result.get("type"),
        "level": result.get("level"),
        "trace": result.get("trace", []),
        "latency_ms": latency_ms,
    }
    _LOG_BUFFER.append(entry)
    if len(_LOG_BUFFER) > MAX_LOG_BUFFER_SIZE:
        del _LOG_BUFFER[: len(_LOG_BUFFER) - MAX_LOG_BUFFER_SIZE]
    _append_log_to_file(entry)


def get_recent_analyze_logs(limit: int = 50, offset: int = 0) -> list[dict]:
    entries = _load_logs_from_file()
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries[offset:offset + limit]


def count_analyze_logs() -> int:
    return len(_load_logs_from_file())
