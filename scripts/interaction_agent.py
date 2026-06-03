from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
SOURCE = "none"  # 단일 방식 고정
MAX_ATTEMPTS = 8

EXPECTED_COLUMNS = [
    "Index",
    "Scenario ID",
    "Question",
    "Expected Level",
    "Model",
    "Source",
    "Pred Level",
    "Doctor Summary",
    "Doctor Detail",
    "Pharmacist Summary",
    "Pharmacist Detail",
    "Alternatives",
    "Latency (s)",
    "Prompt Tokens",
    "Output Tokens",
    "Search Queries",
    "DUR Hits",
    "JSON Mode",
    "Raw JSON",
    "Error",
]

# MOCK_ANALYSIS_RESULT(user_scenario.md) 형태를 강제하는 JSON 스키마.
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "level": {"type": "string", "enum": ["safe", "caution", "danger"]},
        "doctorOpinion": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["summary", "detail"],
        },
        "pharmacistOpinion": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["summary", "detail"],
        },
        "alternatives": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["level", "doctorOpinion", "pharmacistOpinion", "alternatives"],
}

ANALYSIS_RULES = (
    "당신은 50~60대 사용자를 돕는 약물·영양제·음식 상호작용 안내 도우미입니다.\n"
    "아래 사용자의 약물 프로필과 질문을 바탕으로, 질문한 항목을 함께 드셔도 되는지 판단하세요.\n"
    "\n"
    "[판단 규칙]\n"
    "- level은 반드시 'safe' / 'caution' / 'danger' 중 하나로만.\n"
    "- 등급 정의:\n"
    "  · danger(위험): 함께 섭취를 피해야 하는 급성·심각 위해. 출혈, 심장 리듬 이상(QT 연장·부정맥), "
    "세로토닌 증후군, 혈압 급상승, 심한 간·신장 손상처럼 되돌리기 어렵거나 생명에 위협이 될 수 있는 경우.\n"
    "  · caution(주의): 복용 시간 간격을 두거나 양·복용법을 조절하면 관리되는 경우. "
    "흡수율 저하(약효 감소), 경미~중등도 부작용 증가 등 → 회피가 아니라 '시간 띄우기·모니터링'으로 대응.\n"
    "  · safe(안전): 알려진 상호작용이 전혀 없고 일반적인 섭취량에서 문제되지 않는 경우.\n"
    "- [중요 정책] 이 서비스는 상호작용 '경고' 도우미입니다. 근거상 어떤 상호작용이라도 있으면"
    "(흡수율 저하처럼 시간 간격으로 관리되는 경미한 것 포함) **최소 caution**으로 안내하세요. "
    "safe는 알려진 상호작용이 전혀 없을 때만 사용합니다.\n"
    "- 위험을 과소평가하지 마세요. 단, 시간 간격으로 관리되는 흡수저하 등을 danger로 과장하지도 마세요"
    "(이런 경우는 caution). 정말 애매하면 한 단계 보수적으로 판단.\n"
    "[작성 규칙]\n"
    "- 어려운 의학용어 금지. 50~60대가 바로 이해할 쉬운 말로.\n"
    "- 각 summary는 한 문장(40자 이내). 각 detail은 2~4문장.\n"
    "- doctorOpinion은 몸에 생길 수 있는 변화 중심, pharmacistOpinion은 복용 방법·시간 간격 중심.\n"
    "- 진단·처방이 아니며 증상이 있으면 의사·약사와 상담하라는 취지를 detail에 자연스럽게 포함.\n"
    "- alternatives는 더 안전한 대체 식품/영양제 0~3개. safe면 빈 배열도 가능.\n"
    "- 추측성 수치나 출처 불명 정보 금지.\n"
)

# 구조화 출력 방식: responseFormat(Gemini 3) 우선, 실패 시 legacy responseSchema.
_STRUCT_STYLE: str | None = None


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


# ---------------------------------------------------------------------------
# 프롬프트 구성
# ---------------------------------------------------------------------------

def age_band(birth_year: int | None) -> str:
    if not birth_year:
        return "미상"
    age = 2026 - int(birth_year)
    decade = (age // 10) * 10
    return f"{decade}대"


def gender_kr(gender: str) -> str:
    return {"female": "여성", "male": "남성"}.get(gender, "미상")


def format_profile(scenario: dict[str, Any]) -> str:
    user = scenario.get("user") or {}
    health = scenario.get("health") or {}
    lines: list[str] = []
    lines.append("[사용자 정보]")
    lines.append(
        f"- 나이대: {age_band(user.get('birthYear'))} / 성별: {gender_kr(user.get('gender'))}"
    )
    conditions = health.get("conditions") or []
    lines.append(f"- 지병: {', '.join(conditions) if conditions else '없음'}")
    allergies = health.get("allergies") or []
    lines.append(f"- 알레르기: {', '.join(allergies) if allergies else '없음'}")

    lines.append("[복용 중인 약]")
    drugs = [
        d
        for p in (scenario.get("prescriptions") or [])
        for d in (p.get("drugs") or [])
    ]
    if drugs:
        for d in drugs:
            usage = d.get("usageName", "")
            ingr = d.get("ingredientName", "")
            lines.append(f"- {usage}: {ingr}")
    else:
        lines.append("- (없음)")

    lines.append("[복용 중인 영양제]")
    supplements = scenario.get("supplements") or []
    if supplements:
        for s in supplements:
            lines.append(f"- {s.get('productName', '')}: {s.get('ingredients', '')}")
    else:
        lines.append("- (없음)")

    return "\n".join(lines)


def build_analysis_prompt(scenario: dict[str, Any]) -> str:
    parts = [ANALYSIS_RULES]
    parts.append("\n" + format_profile(scenario))
    parts.append(f'\n[질문]\n"{scenario.get("question", "")}"')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Gemini 호출
# ---------------------------------------------------------------------------

def build_generation_config(style: str, structured: bool) -> dict[str, Any]:
    cfg: dict[str, Any] = {"temperature": 0}
    if not structured:
        return cfg
    if style == "legacy":
        cfg["responseMimeType"] = "application/json"
        cfg["responseSchema"] = ANALYSIS_SCHEMA
    else:  # responseFormat (Gemini 3)
        cfg["responseFormat"] = {
            "text": {"mimeType": "application/json", "schema": ANALYSIS_SCHEMA}
        }
    return cfg


class BadRequestError(Exception):
    pass


def _post(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """재시도 포함 단일 POST. 성공 시 응답 JSON 반환."""
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            resp = requests.post(
                url, params={"key": api_key}, json=payload, timeout=120
            )
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2 ** attempt * 2)
            continue

        if resp.status_code == 400:
            # responseFormat 미지원 등 → 호출부에서 스타일 폴백 처리
            raise BadRequestError(resp.text[:400])
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            wait = float(retry_after) + 1 if retry_after else 2 ** attempt * 10
            log(f"      ⏳ 429 quota (attempt {attempt+1}/{MAX_ATTEMPTS}), {wait:.1f}s 대기")
            last_error = ValueError("429 quota")
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            last_error = ValueError(f"{resp.status_code} server error")
            time.sleep(2 ** attempt * 5)
            continue

        resp.raise_for_status()
        return resp.json()

    raise RuntimeError(f"Gemini 요청 실패: {last_error}")


def extract_text_usage(data: dict[str, Any]) -> tuple[str, dict[str, int]]:
    """응답에서 (텍스트, usage 토큰) 추출."""
    candidates = data.get("candidates") or []
    if not candidates:
        block = (data.get("promptFeedback") or {}).get("blockReason")
        raise ValueError(f"후보 없음 blockReason={block}")
    candidate = candidates[0]
    content = candidate.get("content") or {}
    parts = content.get("parts") or []
    text = "".join(part.get("text", "") for part in parts).strip()

    usage_meta = data.get("usageMetadata") or {}
    usage = {
        "prompt": int(usage_meta.get("promptTokenCount", 0) or 0),
        "output": int(usage_meta.get("candidatesTokenCount", 0) or 0),
    }
    return text, usage


def parse_analysis_json(text: str) -> dict[str, Any] | None:
    """텍스트에서 분석 JSON 추출·검증. 실패 시 None."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
        cleaned = cleaned.strip()
    # 첫 균형 중괄호 블록 추출
    start = cleaned.find("{")
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    try:
        obj = json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "level" not in obj:
        return None
    return obj


def generate_one(
    api_base: str, model: str, api_key: str, prompt: str
) -> dict[str, Any]:
    """단일 시나리오 생성(미적용 방식). 결과 dict 반환."""
    global _STRUCT_STYLE
    url = f"{api_base}/models/{model}:generateContent"

    def call(structured: bool) -> dict[str, Any]:
        global _STRUCT_STYLE
        styles = [_STRUCT_STYLE] if _STRUCT_STYLE else ["responseFormat", "legacy"]
        last_bad: Exception | None = None
        for style in styles:
            payload: dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": build_generation_config(style, structured),
            }
            try:
                data = _post(url, api_key, payload)
                if structured:
                    _STRUCT_STYLE = style  # 동작 확인된 스타일 고정
                return data
            except BadRequestError as exc:
                last_bad = exc
                continue
        raise ValueError(f"구조화 출력 스타일 모두 실패: {last_bad}")

    start = time.monotonic()
    data = call(structured=True)
    text, usage = extract_text_usage(data)
    parsed = parse_analysis_json(text)
    json_mode = "structured" if parsed is not None else "parse_failed"
    latency = time.monotonic() - start
    return {
        "parsed": parsed,
        "raw": text,
        "json_mode": json_mode,
        "latency": latency,
        "prompt_tokens": usage["prompt"],
        "output_tokens": usage["output"],
    }


# ---------------------------------------------------------------------------
# DataFrame I/O
# ---------------------------------------------------------------------------

def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    ordered = [c for c in EXPECTED_COLUMNS if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered]
    return df[ordered + remaining]


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="상호작용 분석 Agent 생성 러너 (단일 방식: 미적용/parametric)."
    )
    parser.add_argument(
        "--scenarios", default="data/interaction_scenarios.labeled.json",
        help="라벨 포함 시나리오(Expected Level 채움). 라벨 불필요 시 원본 json도 가능.",
    )
    parser.add_argument("--output", default="data/result/interaction_results.xlsx")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--request-interval", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None, help="시나리오 N개만 실행")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(resolve_project_path(args.env_file))

    api_key = (
        args.api_key
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not api_key:
        print("Gemini API 키 없음 (.env GEMINI_API_KEY/GOOGLE_API_KEY)", file=sys.stderr)
        return 1

    scenarios_path = resolve_project_path(args.scenarios)
    output_path = resolve_project_path(args.output)
    if not scenarios_path.exists():
        print(f"시나리오 파일 없음: {scenarios_path}", file=sys.stderr)
        return 1

    scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    if args.limit:
        scenarios = scenarios[: args.limit]

    # 기존 결과 로드
    if output_path.exists():
        df = pd.read_excel(output_path).fillna("")
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    df = ensure_columns(df)

    done: set[str] = set()
    if not args.force:
        for _, row in df.iterrows():
            sid = str(row.get("Scenario ID", "")).strip()
            src = str(row.get("Source", "")).strip()
            err = str(row.get("Error", "")).strip()
            pred = str(row.get("Pred Level", "")).strip()
            if sid and src == SOURCE and not err and pred:
                done.add(sid)

    rows = list(df.to_dict("records"))
    tasks = [sc for sc in scenarios if args.force or sc["id"] not in done]
    log(f"시나리오 {len(scenarios)}개 (방식 {SOURCE}) → 대기 작업 {len(tasks)}건 (모델 {args.model})")

    sent = 0
    for n, scenario in enumerate(tasks, start=1):
        sid = scenario["id"]
        if sent > 0 and args.request_interval > 0:
            time.sleep(args.request_interval)

        prompt = build_analysis_prompt(scenario)
        log(f"[{n}/{len(tasks)}] {sid} 시작")
        base_row = {
            "Index": n,
            "Scenario ID": sid,
            "Question": scenario.get("question", ""),
            "Expected Level": scenario.get("expected_level") or "",
            "Model": args.model,
            "Source": SOURCE,
            "Search Queries": 0,
            "DUR Hits": 0,
        }
        try:
            result = generate_one(args.api_base, args.model, api_key, prompt)
            parsed = result["parsed"] or {}
            doctor = parsed.get("doctorOpinion") or {}
            pharm = parsed.get("pharmacistOpinion") or {}
            row = {
                **base_row,
                "Pred Level": parsed.get("level", ""),
                "Doctor Summary": doctor.get("summary", ""),
                "Doctor Detail": doctor.get("detail", ""),
                "Pharmacist Summary": pharm.get("summary", ""),
                "Pharmacist Detail": pharm.get("detail", ""),
                "Alternatives": " | ".join(parsed.get("alternatives") or []),
                "Latency (s)": round(result["latency"], 2),
                "Prompt Tokens": result["prompt_tokens"],
                "Output Tokens": result["output_tokens"],
                "JSON Mode": result["json_mode"],
                "Raw JSON": result["raw"],
                "Error": "" if parsed else "PARSE_FAILED",
            }
            log(
                f"[{n}/{len(tasks)}] {sid} 완료 | level={row['Pred Level']} "
                f"| {row['Latency (s)']}s | mode={row['JSON Mode']}"
            )
        except Exception as exc:  # noqa: BLE001
            row = {**base_row, "Error": f"ERROR: {exc}", "Pred Level": ""}
            log(f"[{n}/{len(tasks)}] {sid} 실패: {exc}")

        # 기존 동일 (sid, none) 행 교체 or 추가
        rows = [
            r
            for r in rows
            if not (
                str(r.get("Scenario ID", "")) == sid
                and str(r.get("Source", "")) == SOURCE
            )
        ]
        rows.append(row)
        df = ensure_columns(pd.DataFrame(rows))
        save_dataframe(df, output_path)
        sent += 1

    log(f"저장 완료: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
