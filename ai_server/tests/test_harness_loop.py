import asyncio
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


def test_tool_function_dispatch_names_match_policy_and_declarations():
    module = importlib.import_module("app.harness.harness")

    allowed_actions = set(module.HARNESS_POLICY["allowed_actions"])
    declaration_names = {declaration.name for declaration in module.TOOL_DECLARATIONS}
    function_names = set(module._TOOL_FUNCTIONS)

    assert function_names == allowed_actions
    assert declaration_names == allowed_actions


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


def test_call_with_tools_returns_error_when_model_does_not_call_function():
    module = importlib.import_module("app.harness.harness")

    class _NoFunctionCallModels:
        def generate_content(self, **kwargs):
            return type("FakeResponse", (), {"function_calls": []})()

    client = type("FakeClient", (), {"models": _NoFunctionCallModels()})()

    action_name, action_args = module._call_with_tools(
        ["choose an action"],
        module.TOOL_DECLARATIONS,
        client=client,
    )

    assert action_name == "error"
    assert action_args["type"] == "error"
    assert "도구 호출" in action_args["message"]


def test_execute_tool_rejects_action_outside_allowed_actions():
    module = importlib.import_module("app.harness.harness")

    with pytest.raises(PermissionError):
        module.execute_tool("delete_everything", {})


def test_run_agent_returns_error_for_action_outside_allowed_actions(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "delete_everything", {}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "error"
    assert "허용되지 않은" in result["message"]
    assert result["trace"][0]["action"] == "delete_everything"


def test_run_agent_normalizes_error_action_without_type(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "error", {"message": "실패"}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "error"
    assert result["message"] == "실패"
    assert result["trace"][0]["observation"] == {"type": "error", "message": "실패"}


def test_execute_tool_calls_matching_tool_function(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_ask_clarification(reason):
        assert reason == "불명확함"
        return {"clarification_prompt": "불명확함"}

    monkeypatch.setitem(module._TOOL_FUNCTIONS, "ask_clarification", fake_ask_clarification)

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


def test_harness_policy_goal_describes_validate_query_branching():
    module = importlib.import_module("app.harness.harness")

    goal = module.HARNESS_POLICY["goal"]

    assert "is_relevant" in goal
    assert "is_clear" in goal
    assert "reject" in goal
    assert "ask_clarification" in goal


def test_run_agent_lets_agent_choose_reject_after_validate_query(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "오늘 날씨 어때?"}),
        ("reject", {"reason": "이 질문은 서비스 범위를 벗어났습니다."}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    calls = []

    def fake_execute_tool(name, args):
        calls.append(name)
        if name == "validate_query":
            return {"is_relevant": False, "is_clear": True, "items": [], "missing_info": []}
        if name == "reject":
            return {"type": "rejection", "message": args["reason"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("오늘 날씨 어때?")

    assert result["type"] == "rejection"
    assert result["message"] == "이 질문은 서비스 범위를 벗어났습니다."
    assert [step["action"] for step in result["trace"]] == ["validate_query", "reject"]
    assert len(calls) <= 2


def test_run_agent_rejects_irrelevant_and_unclear_question(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "이거요"}),
        ("reject", {"reason": "질문이 모호하고 서비스 범위를 벗어났습니다."}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": False, "is_clear": False, "items": [], "missing_info": ["대상"]}
        if name == "reject":
            return {"type": "rejection", "message": args["reason"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("이거요")

    assert result["type"] == "rejection"


def test_run_agent_lets_agent_choose_ask_clarification_after_validate_query(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "이거 먹어도 돼요?"}),
        ("ask_clarification", {"reason": "섭취하려는 항목을 알려주세요."}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    calls = []

    def fake_execute_tool(name, args):
        calls.append(name)
        if name == "validate_query":
            return {
                "is_relevant": True,
                "is_clear": False,
                "items": [],
                "missing_info": ["섭취하려는 항목"],
            }
        if name == "ask_clarification":
            return {"clarification_prompt": args["reason"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("이거 먹어도 돼요?")

    assert result["clarification_prompt"] == "섭취하려는 항목을 알려주세요."
    assert [step["action"] for step in result["trace"]] == ["validate_query", "ask_clarification"]
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
            "doctorOpinion": {
                "summary": "요약",
                "detail": "혈압약과 함께 먹어도 큰 문제는 없습니다. 다만 컨디션 변화를 살펴보세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "복용 시간 간격을 2시간 정도 두면 더 안전합니다. 추가 증상이 있으면 의사나 약사와 상담하세요.",
            },
            "alternatives": [],
        },
        "finish": {
            "type": "analysis",
            "level": "safe",
            "doctorOpinion": {
                "summary": "요약",
                "detail": "혈압약과 함께 먹어도 큰 문제는 없습니다. 다만 컨디션 변화를 살펴보세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "복용 시간 간격을 2시간 정도 두면 더 안전합니다. 추가 증상이 있으면 의사나 약사와 상담하세요.",
            },
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
    assert "items" not in result


def test_run_agent_includes_client_context_as_supplementary_info(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    captured = {}

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        captured["messages"] = list(messages)
        return "reject", {"reason": "테스트"}

    def fake_execute_tool(name, args):
        return {"type": "rejection", "message": args["reason"]}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    module.run_agent("질문", extra_context="기존 클라이언트가 보낸 참고 정보")

    assert "기존 클라이언트가 보낸 참고 정보" in captured["messages"][0]
    assert "보조" in captured["messages"][0]


def test_run_agent_backfills_finish_result_with_missing_analyze_fields(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "홍삼 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {
            "result": {
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "혈압약과 함께 먹으면 흡수가 줄어들 수 있습니다. 복용 시간을 2시간 이상 띄우는 것이 좋습니다.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "약 복용 후 2시간 간격을 두고 섭취하세요. 추가로 궁금한 점은 의사나 약사와 상담하세요.",
                },
            },
        }),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    analyze_observation = {
        "level": "caution",
        "doctorOpinion": {
            "summary": "기존 요약",
            "detail": "기존 detail",
        },
        "pharmacistOpinion": {
            "summary": "기존 요약",
            "detail": "기존 detail",
        },
        "alternatives": ["대체 식품"],
    }

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "analyze":
            return analyze_observation
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "analysis"
    assert result["level"] == "caution"
    assert result["alternatives"] == ["대체 식품"]
    assert "복용 시간" in result["doctorOpinion"]["detail"]


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


def test_evaluate_multi_item_fails_when_any_item_detail_is_too_short():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "items": [
            {
                "name": "홍삼",
                "level": "caution",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가 복용 약이 있으면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
            {
                "name": "비타민C",
                "level": "safe",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "괜찮습니다.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "복용 시간은 평소처럼 유지하세요. 불편하면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
        ],
    }

    passed, score, issues = module.evaluate(result, "홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert passed is False
    assert score < 70
    assert issues


def test_evaluate_multi_item_fails_when_any_item_lacks_action_guidance():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "items": [
            {
                "name": "홍삼",
                "level": "caution",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가 복용 약이 있으면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
            {
                "name": "비타민C",
                "level": "safe",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "일반적인 섭취량에서는 큰 문제가 알려져 있지 않습니다. 불편한 증상이 있으면 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "현재 드시는 약을 약사에게 알려주세요. 몸 상태가 달라지면 상담을 받으세요.",
                },
                "alternatives": [],
            },
        ],
    }

    passed, score, issues = module.evaluate(result, "홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert passed is False
    assert score < 70
    assert issues


def test_evaluate_multi_item_fails_when_any_item_lacks_consultation_guidance():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "items": [
            {
                "name": "홍삼",
                "level": "caution",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가 복용 약이 있으면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
            {
                "name": "비타민C",
                "level": "safe",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "일반적인 섭취량에서는 큰 문제가 알려져 있지 않습니다. 불편한 증상이 있으면 잠시 중단하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "식후에 드시고 하루 권장량을 넘기지 마세요. 몸 상태가 달라지면 확인이 필요합니다.",
                },
                "alternatives": [],
            },
        ],
    }

    passed, score, issues = module.evaluate(result, "홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert passed is False
    assert score < 70
    assert issues


def test_evaluate_multi_item_passes_when_all_items_meet_quality_bar():
    module = importlib.import_module("app.harness.harness")

    result = {
        "level": "caution",
        "items": [
            {
                "name": "홍삼",
                "level": "caution",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가 복용 약이 있으면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
            {
                "name": "비타민C",
                "level": "safe",
                "doctorOpinion": {
                    "summary": "요약",
                    "detail": "일반적인 섭취량에서는 큰 문제가 알려져 있지 않습니다. 불편한 증상이 있으면 의사와 상담하세요.",
                },
                "pharmacistOpinion": {
                    "summary": "요약",
                    "detail": "식후 복용 시간에 맞춰 드시고 하루 권장량을 넘기지 마세요. 궁금하면 약사와 상담하세요.",
                },
                "alternatives": [],
            },
        ],
    }

    passed, score, issues = module.evaluate(result, "홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert passed is True
    assert score >= 70
    assert issues == []


def test_run_agent_retries_analysis_after_failed_self_evaluation(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    short_result = {
        "level": "safe",
        "doctorOpinion": {"summary": "요약", "detail": "괜찮습니다."},
        "pharmacistOpinion": {"summary": "요약", "detail": "주의하세요."},
        "alternatives": [],
    }
    long_result = {
        "level": "safe",
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

    planned_actions = iter([
        ("validate_query", {"question": "홍삼 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": short_result}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": long_result}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "analyze":
            return {}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "analysis"
    assert "복용 시간" in result["doctorOpinion"]["detail"]
    assert len(result["trace"]) == 6


def test_run_episode_returns_finish_action_and_observation(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "홍삼 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {"level": "safe"}}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "analyze":
            return {"level": "safe", "doctorOpinion": {}, "pharmacistOpinion": {}, "alternatives": []}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    messages = ["initial"]
    trace = []
    action_name, observation = module._run_episode(messages, trace)

    assert action_name == "finish"
    assert observation["type"] == "analysis"
    assert len(trace) == 4


def test_run_episode_returns_error_when_max_steps_exceeded(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "gather_context", {}

    def fake_execute_tool(name, args):
        return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    messages = ["initial"]
    trace = []
    action_name, observation = module._run_episode(messages, trace)

    assert action_name == "error"
    assert observation == {"type": "error", "message": "분석 한도 초과"}
    assert len(trace) == module.HARNESS_POLICY["max_steps"]


def test_run_agent_grants_fresh_max_steps_budget_on_self_evaluate_retry(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    short_result = {
        "level": "safe",
        "doctorOpinion": {"summary": "요약", "detail": "괜찮습니다."},
        "pharmacistOpinion": {"summary": "요약", "detail": "주의하세요."},
        "alternatives": [],
    }
    long_result = {
        "level": "safe",
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

    planned_actions = iter([
        ("validate_query", {"question": "홍삼 먹어도 되나요?"}),
        ("gather_context", {}),
        ("gather_context", {}),
        ("gather_context", {}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": short_result}),
        ("analyze", {"question": "홍삼 먹어도 되나요?", "context": ""}),
        ("finish", {"result": long_result}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "analyze":
            return {}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected tool call: {name}")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "analysis"
    assert "복용 시간" in result["doctorOpinion"]["detail"]
    assert len(result["trace"]) == 9


def test_run_agent_skips_self_evaluate_for_rejection(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "오늘 날씨 어때?"}),
        ("reject", {"reason": "이 질문은 서비스 범위를 벗어났습니다."}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": False, "is_clear": True, "items": [], "missing_info": []}
        if name == "reject":
            return {"type": "rejection", "message": args["reason"]}
        raise AssertionError(f"unexpected tool call: {name}")

    def fake_evaluate(observation, question):
        raise AssertionError("evaluate should not be called for a rejection")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "evaluate", fake_evaluate)

    result = module.run_agent("오늘 날씨 어때?")

    assert result["type"] == "rejection"


def test_run_agent_skips_self_evaluate_when_max_steps_exceeded(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return "gather_context", {}

    def fake_execute_tool(name, args):
        return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}

    def fake_evaluate(observation, question):
        raise AssertionError("evaluate should not be called when max_steps is exceeded")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "evaluate", fake_evaluate)

    result = module.run_agent("홍삼 먹어도 되나요?")

    assert result["type"] == "error"


def test_run_sub_agents_calls_analyze_item_in_parallel_and_preserves_order(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    calls = []

    def fake_analyze_item(item, context):
        calls.append(item)
        return {
            "name": item,
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "상세"},
            "pharmacistOpinion": {"summary": "요약", "detail": "상세"},
            "alternatives": [],
        }

    monkeypatch.setattr(module, "analyze_item", fake_analyze_item)

    results = asyncio.run(module.run_sub_agents(["홍삼", "비타민C"], "고혈압약 복용 중"))

    assert [r["name"] for r in results] == ["홍삼", "비타민C"]
    assert set(calls) == {"홍삼", "비타민C"}


def test_run_agent_returns_items_and_aggregated_level_for_multi_item_question(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    item_results = [
        {
            "name": "홍삼",
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "혈압약 효과가 줄어들 수 있습니다. 복용 후 변화를 살펴보세요."},
            "pharmacistOpinion": {"summary": "요약", "detail": "복용 시간을 2시간 띄우세요. 의사나 약사와 상담하세요."},
            "alternatives": [],
        },
        {
            "name": "비타민C",
            "level": "danger",
            "doctorOpinion": {"summary": "요약", "detail": "출혈 위험이 커질 수 있습니다. 즉시 복용을 중단하세요."},
            "pharmacistOpinion": {"summary": "요약", "detail": "복용 간격을 두고 의사와 상담하세요. 약사에게도 알리세요."},
            "alternatives": [],
        },
    ]

    planned_actions = iter([
        ("validate_query", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {}}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼", "비타민C"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected tool call: {name}")

    async def fake_run_sub_agents(items, context):
        assert items == ["홍삼", "비타민C"]
        return item_results

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "run_sub_agents", fake_run_sub_agents)

    result = module.run_agent("홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert result["type"] == "analysis"
    assert result["items"] == item_results
    assert result["level"] == "danger"


def test_run_agent_returns_error_when_sub_agents_fail(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    planned_actions = iter([
        ("validate_query", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
    ])

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼", "비타민C"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        raise AssertionError(f"unexpected tool call: {name}")

    def fake_run_sub_agents_sync(items, context):
        raise RuntimeError("sub-agent failed")

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "_run_sub_agents_sync", fake_run_sub_agents_sync)

    result = module.run_agent("홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert result["type"] == "error"
    assert "sub-agent failed" in result["message"]
    assert result["trace"][-1]["action"] == "analyze"


def test_run_agent_reuses_validated_items_when_multi_item_retry_starts_with_analyze(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    short_items = [
        {
            "name": "홍삼",
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "짧습니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "짧습니다."},
            "alternatives": [],
        },
        {
            "name": "비타민C",
            "level": "safe",
            "doctorOpinion": {"summary": "요약", "detail": "짧습니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "짧습니다."},
            "alternatives": [],
        },
    ]
    long_items = [
        {
            "name": "홍삼",
            "level": "caution",
            "doctorOpinion": {
                "summary": "요약",
                "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 불편하면 의사와 상담하세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가로 복용 중인 약이 있으면 약사와 상담하세요.",
            },
            "alternatives": [],
        },
        {
            "name": "비타민C",
            "level": "danger",
            "doctorOpinion": {
                "summary": "요약",
                "detail": "출혈 위험이 커질 수 있어 주의가 필요합니다. 멍이나 출혈이 있으면 의사와 상담하세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "임의로 함께 복용하지 말고 복용 간격을 확인하세요. 약사에게 현재 복용 약을 알려주세요.",
            },
            "alternatives": [],
        },
    ]

    planned_actions = iter([
        ("validate_query", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {}}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {}}),
    ])
    sub_agent_results = iter([short_items, long_items])
    sub_agent_calls = []

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        return next(planned_actions)

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {
                "is_relevant": True,
                "is_clear": True,
                "items": ["홍삼", "비타민C"],
                "missing_info": [],
            }
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected direct tool call: {name}")

    def fake_run_sub_agents_sync(items, context):
        sub_agent_calls.append(list(items))
        item_results = next(sub_agent_results)
        return item_results

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "_run_sub_agents_sync", fake_run_sub_agents_sync)

    result = module.run_agent("홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert sub_agent_calls == [["홍삼", "비타민C"], ["홍삼", "비타민C"]]
    assert result["type"] == "analysis"
    assert result["items"] == long_items
    assert result["level"] == "danger"


def test_run_agent_self_evaluate_retry_message_includes_multi_item_names(monkeypatch):
    module = importlib.import_module("app.harness.harness")

    short_items = [
        {
            "name": "홍삼",
            "level": "caution",
            "doctorOpinion": {"summary": "요약", "detail": "짧습니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "짧습니다."},
            "alternatives": [],
        },
        {
            "name": "비타민C",
            "level": "safe",
            "doctorOpinion": {"summary": "요약", "detail": "짧습니다."},
            "pharmacistOpinion": {"summary": "요약", "detail": "짧습니다."},
            "alternatives": [],
        },
    ]
    long_items = [
        {
            "name": "홍삼",
            "level": "caution",
            "doctorOpinion": {
                "summary": "요약",
                "detail": "혈압약과 함께 먹으면 몸의 반응이 달라질 수 있습니다. 복용 전후 변화를 살피고 불편하면 의사와 상담하세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "약 복용 시간과 2시간 이상 간격을 두세요. 추가로 복용 중인 약이 있으면 약사와 상담하세요.",
            },
            "alternatives": [],
        },
        {
            "name": "비타민C",
            "level": "safe",
            "doctorOpinion": {
                "summary": "요약",
                "detail": "일반적인 양에서는 큰 문제가 알려져 있지 않습니다. 불편한 증상이 있으면 의사와 상담하세요.",
            },
            "pharmacistOpinion": {
                "summary": "요약",
                "detail": "기존 약 복용 시간과 간격을 확인하세요. 궁금한 점은 약사와 상담하세요.",
            },
            "alternatives": [],
        },
    ]
    planned_actions = iter([
        ("validate_query", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?"}),
        ("gather_context", {}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {}}),
        ("analyze", {"question": "홍삼이랑 비타민C 같이 먹어도 되나요?", "context": ""}),
        ("finish", {"result": {}}),
    ])
    sub_agent_results = iter([short_items, long_items])
    retry_message = {}

    def fake_call_with_tools(messages, declarations, client=None, model="gemini-3.1-flash-lite"):
        action = next(planned_actions)
        if action[0] == "analyze" and any("[Self-Evaluate]" in message for message in messages):
            retry_message["text"] = messages[-1]
        return action

    def fake_execute_tool(name, args):
        if name == "validate_query":
            return {"is_relevant": True, "is_clear": True, "items": ["홍삼", "비타민C"], "missing_info": []}
        if name == "gather_context":
            return {"drugs": [], "supplements": [], "health_conditions": [], "allergies": []}
        if name == "finish":
            return {"type": "analysis", **args["result"]}
        raise AssertionError(f"unexpected direct tool call: {name}")

    def fake_run_sub_agents_sync(items, context):
        return next(sub_agent_results)

    monkeypatch.setattr(module, "_call_with_tools", fake_call_with_tools)
    monkeypatch.setattr(module, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(module, "_run_sub_agents_sync", fake_run_sub_agents_sync)

    module.run_agent("홍삼이랑 비타민C 같이 먹어도 되나요?")

    assert "홍삼" in retry_message["text"]
    assert "비타민C" in retry_message["text"]
