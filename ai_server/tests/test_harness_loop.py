import importlib

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
