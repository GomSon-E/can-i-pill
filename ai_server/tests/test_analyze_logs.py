from app import analyze_logs


def _use_temp_logs_path(monkeypatch, tmp_path):
    analyze_logs._LOG_BUFFER.clear()
    monkeypatch.setenv("AI_ANALYZE_LOGS_PATH", str(tmp_path / "analyze_logs.jsonl"))


def test_record_analyze_log_appends_to_buffer(monkeypatch, tmp_path):
    _use_temp_logs_path(monkeypatch, tmp_path)

    result = {"type": "analysis", "level": "safe", "trace": []}
    analyze_logs.record_analyze_log("질문입니다", "컨텍스트", result, 123.4)

    assert len(analyze_logs._LOG_BUFFER) == 1
    entry = analyze_logs._LOG_BUFFER[0]
    assert entry["question"] == "질문입니다"
    assert entry["context"] == "컨텍스트"
    assert entry["type"] == "analysis"
    assert entry["level"] == "safe"
    assert entry["trace"] == []
    assert entry["latency_ms"] == 123.4


def test_record_analyze_log_persists_to_file(monkeypatch, tmp_path):
    _use_temp_logs_path(monkeypatch, tmp_path)

    result = {"type": "analysis", "level": "safe", "trace": []}
    analyze_logs.record_analyze_log("질문입니다", "컨텍스트", result, 123.4)
    analyze_logs._LOG_BUFFER.clear()

    logs = analyze_logs.get_recent_analyze_logs()

    assert len(logs) == 1
    assert logs[0]["question"] == "질문입니다"
    assert logs[0]["latency_ms"] == 123.4


def test_get_recent_analyze_logs_orders_by_timestamp_desc_and_respects_limit(monkeypatch, tmp_path):
    _use_temp_logs_path(monkeypatch, tmp_path)

    result = {"type": "analysis", "level": "safe", "trace": []}
    analyze_logs.record_analyze_log("첫번째", "", result, 100.0)
    analyze_logs.record_analyze_log("두번째", "", result, 200.0)
    analyze_logs.record_analyze_log("세번째", "", result, 300.0)
    analyze_logs._LOG_BUFFER.clear()

    logs = analyze_logs.get_recent_analyze_logs(limit=2)

    assert len(logs) == 2
    assert logs[0]["question"] == "세번째"
    assert logs[1]["question"] == "두번째"


def test_record_analyze_log_buffer_is_capped(monkeypatch, tmp_path):
    _use_temp_logs_path(monkeypatch, tmp_path)

    result = {"type": "analysis", "level": "safe", "trace": []}
    for i in range(analyze_logs.MAX_LOG_BUFFER_SIZE + 5):
        analyze_logs.record_analyze_log(f"질문{i}", "", result, 1.0)

    assert len(analyze_logs._LOG_BUFFER) == analyze_logs.MAX_LOG_BUFFER_SIZE
