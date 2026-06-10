import importlib

import httpx


def test_harness_tools_module_is_importable():
    module = importlib.import_module("app.harness.tools")

    assert module is not None


def test_validate_query_marks_weather_question_as_irrelevant(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_generate_validation(question):
        assert question == "오늘 날씨 어때?"
        return {
            "is_relevant": False,
            "is_clear": True,
            "items": [],
            "missing_info": [],
        }

    monkeypatch.setattr(module, "_generate_validation", fake_generate_validation)

    result = module.validate_query("오늘 날씨 어때?")

    assert result["is_relevant"] is False


def test_validate_query_marks_vague_question_as_unclear(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_generate_validation(question):
        assert question == "이거 먹어도 돼요?"
        return {
            "is_relevant": True,
            "is_clear": False,
            "items": [],
            "missing_info": ["섭취하려는 항목"],
        }

    monkeypatch.setattr(module, "_generate_validation", fake_generate_validation)

    result = module.validate_query("이거 먹어도 돼요?")

    assert result["is_clear"] is False
    assert result["missing_info"] == ["섭취하려는 항목"]


def test_validate_query_marks_named_supplement_question_as_clear(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_generate_validation(question):
        assert question == "홍삼 먹어도 되나요?"
        return {
            "is_relevant": True,
            "is_clear": True,
            "items": ["홍삼"],
            "missing_info": [],
        }

    monkeypatch.setattr(module, "_generate_validation", fake_generate_validation)

    result = module.validate_query("홍삼 먹어도 되나요?")

    assert result["is_relevant"] is True
    assert result["is_clear"] is True
    assert result["items"] == ["홍삼"]


def test_gather_context_returns_empty_lists_when_backend_has_no_data(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_fetch_backend_data():
        return [], [], {}

    monkeypatch.setattr(module, "_fetch_backend_data", fake_fetch_backend_data)

    result = module.gather_context()

    assert result == {
        "drugs": [],
        "supplements": [],
        "health_conditions": [],
        "allergies": [],
    }


def test_gather_context_normalizes_populated_backend_data(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_fetch_backend_data():
        prescriptions = [
            {"id": "1", "name": "내과", "drugs": [{"name": "타이레놀"}, {"name": "아스피린"}]}
        ]
        supplements = [{"id": "2", "name": "비타민C", "ingredients": ["비타민C"]}]
        health = {"conditions": ["고혈압"], "allergies": ["페니실린"]}
        return prescriptions, supplements, health

    monkeypatch.setattr(module, "_fetch_backend_data", fake_fetch_backend_data)

    result = module.gather_context()

    assert result == {
        "drugs": ["타이레놀", "아스피린"],
        "supplements": [{"name": "비타민C", "ingredients": ["비타민C"]}],
        "health_conditions": ["고혈압"],
        "allergies": ["페니실린"],
    }


def test_fetch_backend_data_returns_empty_when_backend_unreachable(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    class _FailingClient:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def get(self, path):
            raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(module.httpx, "Client", lambda base_url: _FailingClient())

    prescriptions, supplements, health = module._fetch_backend_data()

    assert prescriptions == []
    assert supplements == []
    assert health == {}


def test_ask_clarification_returns_clarification_prompt():
    module = importlib.import_module("app.harness.tools")

    result = module.ask_clarification("섭취하려는 항목이 명확하지 않습니다")

    assert result == {"clarification_prompt": "섭취하려는 항목이 명확하지 않습니다"}


def test_analyze_returns_level_within_allowed_set(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_generate_analysis(question, context):
        assert question == "홍삼 먹어도 되나요?"
        assert context == "고혈압약 복용 중"
        return {
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "상세 설명입니다. 두 문장입니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "복용 시간을 띄우세요. 약사와 상담하세요."},
            "alternatives": [],
        }

    monkeypatch.setattr(module, "_generate_analysis", fake_generate_analysis)

    result = module.analyze("홍삼 먹어도 되나요?", "고혈압약 복용 중")

    assert result["level"] in ("safe", "caution", "danger")


def test_reject_returns_rejection_type_with_message():
    module = importlib.import_module("app.harness.tools")

    result = module.reject("이 서비스의 분석 범위를 벗어난 질문입니다")

    assert result == {
        "type": "rejection",
        "message": "이 서비스의 분석 범위를 벗어난 질문입니다",
    }


def test_finish_returns_analysis_type_with_result_fields():
    module = importlib.import_module("app.harness.tools")

    result = module.finish({
        "level": "caution",
        "doctorOpinion": {"summary": "요약", "detail": "상세"},
        "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
        "alternatives": [],
    })

    assert result == {
        "type": "analysis",
        "level": "caution",
        "doctorOpinion": {"summary": "요약", "detail": "상세"},
        "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
        "alternatives": [],
    }


def test_analyze_item_returns_name_and_level_within_allowed_set(monkeypatch):
    module = importlib.import_module("app.harness.tools")

    def fake_generate_item_analysis(item, context):
        assert item == "홍삼"
        assert context == "고혈압약 복용 중"
        return {
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "상세 설명입니다. 두 문장입니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "복용 시간을 띄우세요. 약사와 상담하세요."},
            "alternatives": [],
        }

    monkeypatch.setattr(module, "_generate_item_analysis", fake_generate_item_analysis)

    result = module.analyze_item("홍삼", "고혈압약 복용 중")

    assert result["name"] == "홍삼"
    assert result["level"] in ("safe", "caution", "danger")
