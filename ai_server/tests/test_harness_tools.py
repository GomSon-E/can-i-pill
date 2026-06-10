import importlib


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
