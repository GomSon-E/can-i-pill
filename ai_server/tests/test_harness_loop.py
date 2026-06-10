import importlib

import pytest
from google.genai import types


def test_harness_loop_module_is_importable():
    module = importlib.import_module("app.harness.harness")

    assert module is not None


def test_harness_policy_declares_allowed_completion_actions():
    module = importlib.import_module("app.harness.harness")

    policy = module.HARNESS_POLICY

    assert "allowed_actions" in policy
    assert "max_steps" in policy
    assert "completion_conditions" in policy
    assert set(policy["completion_conditions"]).issubset(policy["allowed_actions"])


def test_harness_policy_declares_goal_and_max_steps_for_full_cycle():
    module = importlib.import_module("app.harness.harness")

    policy = module.HARNESS_POLICY

    assert "goal" in policy
    assert isinstance(policy["goal"], str) and policy["goal"]
    assert policy["max_steps"] == 7
    assert {"finish", "reject", "ask_clarification"}.issubset(
        set(policy["completion_conditions"])
    )


class _FakeModels:
    def __init__(self, action_name="ping"):
        self.action_name = action_name
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return type(
            "FakeResponse",
            (),
            {"function_calls": [types.FunctionCall(name=self.action_name, args={"ok": True})]},
        )()


class _FakeClient:
    def __init__(self, action_name="ping"):
        self.models = _FakeModels(action_name=action_name)


def test_call_with_tools_sends_function_declarations_and_returns_action():
    module = importlib.import_module("app.harness.harness")
    client = _FakeClient()
    declaration = types.FunctionDeclaration(
        name="ping",
        description="Return a smoke-test action.",
        parameters_json_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
        },
    )

    action_name, action_args = module._call_with_tools(
        ["choose the ping action"],
        [declaration],
        client=client,
    )

    assert action_name == "ping"
    assert action_args == {"ok": True}
    tools = client.models.kwargs["config"].tools
    assert tools[0].function_declarations == [declaration]


def test_tool_declarations_define_all_allowed_agent_actions():
    module = importlib.import_module("app.harness.harness")

    declarations = module.TOOL_DECLARATIONS

    assert [declaration.name for declaration in declarations] == [
        "validate_query",
        "gather_context",
        "ask_clarification",
        "analyze",
        "reject",
        "finish",
    ]
    for declaration in declarations:
        assert declaration.description
        assert declaration.parameters_json_schema["type"] == "object"


def test_call_with_tools_accepts_allowed_action_from_model():
    module = importlib.import_module("app.harness.harness")
    client = _FakeClient(action_name="validate_query")

    action_name, action_args = module._call_with_tools(
        ["choose an allowed action"],
        module.TOOL_DECLARATIONS,
        client=client,
    )

    assert action_name in module.HARNESS_POLICY["allowed_actions"]
    assert action_args == {"ok": True}


def test_execute_tool_rejects_action_outside_allowed_actions():
    module = importlib.import_module("app.harness.harness")

    with pytest.raises(PermissionError):
        module.execute_tool("delete_everything", {})


def test_execute_tool_calls_matching_tool_function(monkeypatch):
    module = importlib.import_module("app.harness.harness")
    tools = importlib.import_module("app.harness.tools")

    def fake_ask_clarification(reason):
        assert reason == "불명확함"
        return {"clarification_prompt": "불명확함"}

    monkeypatch.setattr(tools, "ask_clarification", fake_ask_clarification)
    monkeypatch.setattr(module, "ask_clarification", fake_ask_clarification)

    result = module.execute_tool("ask_clarification", {"reason": "불명확함"})

    assert result == {"clarification_prompt": "불명확함"}


def test_run_agent_returns_error_when_max_steps_exceeded(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "gather_context", {}

    def fake_execute_tool(name, args):
        return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "error"
    assert result["message"] == "분석 한도 초과"
    assert len(result["trace"]) == module.HARNESS_POLICY["max_steps"]
    assert result["trace"][0] == {
        "action": "gather_context",
        "args": {},
        "observation": {
            "drugs": [],
            "supplements": [],
            "health_conditions": [],
            "allergies": [],
        },
    }


def test_run_agent_rejects_irrelevant_question_within_two_steps(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "validate_query", {"question": "오늘 날씨 어때?"}

    calls = []

    def fake_execute_tool(name, args):
        calls.append(name)
        assert name == "validate_query"
        return {"is_relevant": False, "is_clear": True, "items": [], "missing_info": []}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("오늘 날씨 어때?")

    assert result["type"] == "rejection"
    assert len(calls) <= 2


def test_run_agent_rejects_irrelevant_and_unclear_question(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "validate_query", {"question": "이거요"}

    def fake_execute_tool(name, args):
        return {"is_relevant": False, "is_clear": False, "items": [], "missing_info": ["대상"]}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("이거요")

    assert result["type"] == "rejection"


def test_run_agent_asks_clarification_for_unclear_question_within_two_steps(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "validate_query", {"question": "이거 먹어도 돼요?"}

    calls = []

    def fake_execute_tool(name, args):
        calls.append(name)
        assert name == "validate_query"
        return {
            "is_relevant": True,
            "is_clear": False,
            "items": [],
            "missing_info": ["섭취하려는 항목"],
        }

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("이거 먹어도 돼요?")

    assert "clarification_prompt" in result
    assert len(calls) <= 2


def test_run_agent_returns_analysis_for_clear_relevant_question(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "홍삼 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {"level": "safe"}}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    observations = {
        "validate_query": {
            "is_relevant": True,
            "is_clear": True,
            "items": ["홍삼"],
            "missing_info": [],
        },
        "gather_context": {
            "drugs": [],
            "supplements": [],
            "health_conditions": [],
            "allergies": [],
        },
        "analyze": {
            "level": "safe",
            "doctorOpinion": {"summary": "요약", "detail": "상세"},
            "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
            "alternatives": [],
        },
        "finish": {
            "type": "analysis",
            "level": "safe",
            "doctorOpinion": {"summary": "요약", "detail": "상세"},
            "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
            "alternatives": [],
        },
    }

    def fake_execute_tool(name, args):
        return observations[name]

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "analysis"
    assert result["level"] == "safe"
    assert [step["action"] for step in result["trace"]] == [
        "validate_query",
        "gather_context",
        "analyze",
        "finish",
    ]
    assert result["trace"][0]["args"] == {"question": "홍삼 먹어도 되나요?"}
    assert result["trace"][0]["observation"]["is_relevant"] is True


def test_evaluate_short_detail_scores_below_70():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "doctorOpinion": {"summary": "요약", "detail": "괜찮습니다."},
        "pharmacistOpinion": {"summary": "요약", "detail": "주의하세요."},
        "alternatives": [],
    }

    passed, score, issues = module.evaluate(result, "홍삼 먹어도 되나요?")

    assert passed is False
    assert score < 70
    assert issues


def test_evaluate_sufficient_detail_with_guidance_and_consultation_scores_at_least_70():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "doctorOpinion": {
            "summary": "요약",
            "detail": "혈압약과 함께 먹으면 흡수가 줄어들 수 있습니다. 복용 시간을 2시간 이상 띄우는 것이 좋습니다.",
        },
        "pharmacistOpinion": {
            "summary": "요약",
            "detail": "약 복용 후 2시간 간격을 두고 섭취하세요. 추가로 궁금한 점은 의사나 약사와 상담하세요.",
        },
        "alternatives": [],
    }

    passed, score, issues = module.evaluate(result, "홍삼 먹어도 되나요?")

    assert passed is True
    assert score >= 70
    assert issues == []
