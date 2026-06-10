import asyncio
import re
import threading

from google.genai import types

from app.harness.tools import (
    validate_query,
    gather_context,
    ask_clarification,
    analyze,
    analyze_item,
    reject,
    finish,
)


HARNESS_POLICY = {
    "goal": (
        "사용자의 약물·영양제·음식 상호작용 질문에 대해 "
        "validate_query → gather_context → analyze → finish 순서로 분석하고, "
        "필요 시 self-evaluate 재시도(최대 2회)를 거쳐 답변 품질을 보장한다.\n"
        "validate_query 관측 결과를 직접 보고 다음 action을 선택하라: "
        "is_relevant가 false이면 reject를 선택하고, "
        "is_relevant가 true이지만 is_clear가 false이면 missing_info를 바탕으로 "
        "ask_clarification을 선택하라. is_relevant와 is_clear가 모두 true이면 "
        "gather_context로 진행하라."
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


async def run_sub_agents(items: list, context: str) -> list:
    return await asyncio.gather(
        *(asyncio.to_thread(analyze_item, item, context) for item in items)
    )


def _run_sub_agents_sync(items: list, context: str) -> list:
    box = {}

    def runner():
        try:
            box["result"] = asyncio.run(run_sub_agents(items, context))
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if "error" in box:
        raise box["error"]
    return box["result"]


_LEVEL_RANK = {"safe": 0, "caution": 1, "danger": 2}


def _aggregate_level(items: list) -> str:
    return max((item.get("level", "safe") for item in items), key=lambda level: _LEVEL_RANK.get(level, 0))


_MAX_SELF_EVALUATE_RETRIES = 2


def _run_episode(messages, trace):
    last_analyze_result = None
    items = []

    for _ in range(HARNESS_POLICY["max_steps"]):
        action_name, action_args = _call_with_tools(messages, TOOL_DECLARATIONS)

        if action_name == "finish" and last_analyze_result:
            action_args = {"result": {**last_analyze_result, **(action_args.get("result") or {})}}

        if action_name == "analyze" and len(items) >= 2:
            item_results = _run_sub_agents_sync(items, action_args.get("context", ""))
            observation = {"items": item_results, "level": _aggregate_level(item_results)}
        else:
            observation = execute_tool(action_name, action_args)

        trace.append({"action": action_name, "args": action_args, "observation": observation})
        messages.append(f"[Action] {action_name}({action_args})")
        messages.append(f"[Observation] {observation}")

        if action_name == "validate_query":
            items = observation.get("items") or []

        if action_name == "analyze":
            last_analyze_result = observation

        if action_name in HARNESS_POLICY["completion_conditions"]:
            return action_name, observation

    return "error", {"type": "error", "message": "분석 한도 초과"}


def run_agent(question: str, extra_context: str = "") -> dict:
    initial_message = f"{HARNESS_POLICY['goal']}\n\n[사용자 질문]\n{question}"
    if extra_context:
        initial_message += (
            f"\n\n[클라이언트 제공 보조 정보 - 참고용, gather_context 결과보다 우선순위 낮음]\n{extra_context}"
        )
    messages = [initial_message]
    trace = []
    eval_retries = 0
    task_completed = False

    while not task_completed:
        action_name, observation = _run_episode(messages, trace)

        if action_name == "finish":
            passed, score, issues = evaluate(observation, question)
            if not passed and eval_retries < _MAX_SELF_EVALUATE_RETRIES:
                eval_retries += 1
                messages.append(
                    f"[Self-Evaluate] score={score}, issues={issues}. "
                    "답변 품질이 기준에 못 미칩니다. 위 문제를 보완해 analyze를 다시 호출하고 "
                    "더 자세한 detail과 행동 지침, 상담 권유 문구를 포함하세요."
                )
                continue

        task_completed = True

    result = dict(observation)
    result["trace"] = trace
    return result


_ACTION_GUIDANCE_KEYWORDS = ["복용", "시간", "간격", "용법", "식전", "식후"]
_CONSULTATION_KEYWORDS = ["의사", "약사"]


def _sentence_count(text: str) -> int:
    return len([s for s in re.split(r"[.!?]", text) if s.strip()])


def evaluate(result: dict, question: str) -> tuple:
    score = 100
    issues = []

    items = result.get("items")
    if items:
        doctor_detail = " ".join(item.get("doctorOpinion", {}).get("detail", "") for item in items)
        pharmacist_detail = " ".join(item.get("pharmacistOpinion", {}).get("detail", "") for item in items)
    else:
        doctor_detail = result.get("doctorOpinion", {}).get("detail", "")
        pharmacist_detail = result.get("pharmacistOpinion", {}).get("detail", "")
    combined = f"{doctor_detail} {pharmacist_detail}"

    if _sentence_count(doctor_detail) < 2 or _sentence_count(pharmacist_detail) < 2:
        score -= 20
        issues.append("detail은 2문장 이상으로 작성해야 합니다.")

    if not any(keyword in combined for keyword in _ACTION_GUIDANCE_KEYWORDS):
        score -= 20
        issues.append("복용 시간·간격 등 행동 지침이 포함되어야 합니다.")

    if not any(keyword in combined for keyword in _CONSULTATION_KEYWORDS):
        score -= 20
        issues.append("의사·약사 상담 권유 문구가 포함되어야 합니다.")

    return score >= 70, score, issues
