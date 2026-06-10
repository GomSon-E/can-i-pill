from google.genai import types

from app.harness.tools import (
    validate_query,
    gather_context,
    ask_clarification,
    analyze,
    reject,
    finish,
)


HARNESS_POLICY = {
    "goal": (
        "사용자의 약물·영양제·음식 상호작용 질문에 대해 "
        "validate_query → gather_context → analyze → finish 순서로 분석하고, "
        "필요 시 self-evaluate 재시도(최대 2회)를 거쳐 답변 품질을 보장한다."
    ),
    "allowed_actions": [
        "validate_query",
        "gather_context",
        "ask_clarification",
        "analyze",
        "reject",
        "finish",
    ],
    "max_steps": 7,
    "completion_conditions": ["finish", "reject", "ask_clarification"],
}


TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="validate_query",
        description="Check whether the question is relevant and clear enough.",
        parameters_json_schema={
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    ),
    types.FunctionDeclaration(
        name="gather_context",
        description="Load the current in-memory user medication context.",
        parameters_json_schema={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="ask_clarification",
        description="Ask a follow-up question when the user request is unclear.",
        parameters_json_schema={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    ),
    types.FunctionDeclaration(
        name="analyze",
        description="Analyze interaction risk using the question and context.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "context": {"type": "string"},
            },
            "required": ["question", "context"],
        },
    ),
    types.FunctionDeclaration(
        name="reject",
        description="Reject questions outside the service scope.",
        parameters_json_schema={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    ),
    types.FunctionDeclaration(
        name="finish",
        description="Return the final analysis result.",
        parameters_json_schema={
            "type": "object",
            "properties": {"result": {"type": "object"}},
            "required": ["result"],
        },
    ),
]


def _call_with_tools(messages, tool_declarations, client=None, model="gemini-3.1-flash-lite"):
    if client is None:
        from app.routers.ai import _client as client

    response = client.models.generate_content(
        model=model,
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=tool_declarations)],
        ),
    )
    function_calls = response.function_calls or []
    first_call = function_calls[0]
    return first_call.name, first_call.args or {}


_TOOL_FUNCTIONS = {
    "validate_query": validate_query,
    "gather_context": gather_context,
    "ask_clarification": ask_clarification,
    "analyze": analyze,
    "reject": reject,
    "finish": finish,
}


def execute_tool(name, args):
    if name not in HARNESS_POLICY["allowed_actions"]:
        raise PermissionError(f"Action '{name}' is not allowed")

    return _TOOL_FUNCTIONS[name](**args)
