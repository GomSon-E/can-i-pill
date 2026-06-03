from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from interaction_agent import (
    DEFAULT_API_BASE,
    BadRequestError,
    ANALYSIS_SCHEMA,  # noqa: F401 (참고용)
    build_generation_config,
    extract_text_usage,
    format_profile,
    load_env_file,
    log,
    resolve_project_path,
    _post,
)

LEVEL_ORDER = {"safe": 0, "caution": 1, "danger": 2}
LEVELS = ["safe", "caution", "danger"]

DEFAULT_JUDGE_MODEL = "gemini-3.1-pro-preview"  # 생성(lite)과 다른 독립 모델

# ── 비용 단가(USD) — 게시 요율로 갱신 필요(placeholder) ────────────────────
# per 1,000,000 tokens. Google Search 그라운딩: $14 / 1,000 쿼리.
PRICING: dict[str, dict[str, float]] = {
    "gemini-3.1-flash-lite": {"input": 0.10, "output": 0.40},
    "gemini-3-flash-preview": {"input": 0.30, "output": 2.50},
    "gemini-3.1-pro-preview": {"input": 1.25, "output": 10.00},
}
SEARCH_COST_PER_QUERY = 14.0 / 1000.0  # $0.014

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "factuality": {"type": "integer"},
                "readability": {"type": "integer"},
                "usefulness": {"type": "integer"},
                "schema": {"type": "integer"},
            },
            "required": [
                "factuality",
                "readability",
                "usefulness",
                "schema",
            ],
        },
        "rationale": {"type": "string"},
        "jargon_terms_found": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["scores", "rationale", "jargon_terms_found"],
}

JUDGE_RULES = (
    "당신은 약물 상호작용 안내 답변의 '글 품질'을 평가하는 엄격한 심사위원입니다.\n"
    "아래 사용자 프로필·질문·후보 답변(JSON)을 보고 각 항목을 1~5점(정수)으로 채점하세요.\n"
    "※ 위험도 등급(level: safe/caution/danger)의 적정성은 평가하지 마세요(별도 정확도 지표로 측정함). "
    "오직 답변 '본문'의 품질만 보세요.\n"
    "- factuality(사실성/무환각): 약리 상식에 부합하고 날조된 수치·근거나 사실 오류(환각)가 없는가. "
    "(level이 맞고 틀리고는 보지 말고, 본문에 적힌 설명이 사실인지만 판단)\n"
    "- readability(가독성): 50~60대가 이해할 쉬운 말인가. 번역 안 된 의학용어가 있으면 감점.\n"
    "- usefulness(유용성): 복용 시간 간격·대안 등 구체적이고 실행 가능한가.\n"
    "- schema(스키마+면책): 의사·약사 소견/대안 형식이 갖춰지고 면책 취지가 있는가.\n"
    "jargon_terms_found에는 답변에서 발견된 어려운 의학용어를 나열하세요(없으면 빈 배열).\n"
)


# ---------------------------------------------------------------------------
# 구조화 호출 (judge / 일반)
# ---------------------------------------------------------------------------

_JUDGE_STYLE: str | None = None


def parse_first_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3]
    start = cleaned.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def call_gemini_judge(
    api_base: str, model: str, api_key: str, prompt: str
) -> dict[str, Any]:
    global _JUDGE_STYLE
    url = f"{api_base}/models/{model}:generateContent"
    styles = [_JUDGE_STYLE] if _JUDGE_STYLE else ["responseFormat", "legacy"]
    last_bad: Exception | None = None
    for style in styles:
        cfg: dict[str, Any] = {"temperature": 0}
        if style == "legacy":
            cfg["responseMimeType"] = "application/json"
            cfg["responseSchema"] = JUDGE_SCHEMA
        else:
            cfg["responseFormat"] = {
                "text": {"mimeType": "application/json", "schema": JUDGE_SCHEMA}
            }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": cfg,
        }
        try:
            data = _post(url, api_key, payload)
            _JUDGE_STYLE = style
            text, _ = extract_text_usage(data)
            parsed = parse_first_json(text)
            if parsed:
                return parsed
            raise ValueError("judge JSON 파싱 실패")
        except BadRequestError as exc:
            last_bad = exc
            continue
    raise ValueError(f"judge 호출 실패: {last_bad}")


def call_claude_judge(model: str, api_key: str, prompt: str) -> dict[str, Any]:
    """Anthropic Messages API judge(선택). ANTHROPIC_API_KEY 있을 때만."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": prompt
                + "\n\n반드시 JSON 객체만 출력하세요(스키마: scores{factuality,"
                "readability,usefulness,schema}, rationale, jargon_terms_found).",
            }
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    parsed = parse_first_json(text)
    if not parsed:
        raise ValueError("claude judge JSON 파싱 실패")
    return parsed


# ---------------------------------------------------------------------------
# Judge 프롬프트
# ---------------------------------------------------------------------------

def build_judge_prompt(
    scenario: dict[str, Any], candidate: dict[str, Any]
) -> str:
    # 레벨 누출 방지: expected_level/메모는 프롬프트에 넣지 않는다(글 품질만 평가).
    parts = [
        JUDGE_RULES,
        "\n" + format_profile(scenario),
        f'\n[질문]\n"{scenario.get("question", "")}"',
        "\n[후보 답변(JSON)]\n" + json.dumps(candidate, ensure_ascii=False, indent=2),
    ]
    return "\n".join(parts)


def row_to_candidate(row: dict[str, Any]) -> dict[str, Any]:
    alts = str(row.get("Alternatives", "") or "")
    return {
        "level": row.get("Pred Level", ""),
        "doctorOpinion": {
            "summary": row.get("Doctor Summary", ""),
            "detail": row.get("Doctor Detail", ""),
        },
        "pharmacistOpinion": {
            "summary": row.get("Pharmacist Summary", ""),
            "detail": row.get("Pharmacist Detail", ""),
        },
        "alternatives": [a.strip() for a in alts.split("|") if a.strip()],
    }


# ---------------------------------------------------------------------------
# 지표 계산
# ---------------------------------------------------------------------------

def level_metrics(sub: pd.DataFrame) -> dict[str, Any]:
    """expected_level 라벨된 행만 대상으로 정확도 지표 계산."""
    labeled = sub[(sub["Expected Level"] != "") & (sub["Pred Level"] != "")]
    n = len(labeled)
    if n == 0:
        return {"labeled": 0}
    correct = int((labeled["Expected Level"] == labeled["Pred Level"]).sum())

    # 혼동행렬
    confusion = {e: {p: 0 for p in LEVELS} for e in LEVELS}
    under = 0  # 과소경고: expected danger인데 pred가 덜 심각
    over = 0   # 과대경고: pred가 더 심각
    danger_total = 0
    for _, r in labeled.iterrows():
        e, p = r["Expected Level"], r["Pred Level"]
        if e in confusion and p in confusion[e]:
            confusion[e][p] += 1
        if e in LEVEL_ORDER and p in LEVEL_ORDER:
            if LEVEL_ORDER[p] < LEVEL_ORDER[e]:
                under += 1
            elif LEVEL_ORDER[p] > LEVEL_ORDER[e]:
                over += 1
        if e == "danger":
            danger_total += 1
    danger_underwarn = sum(
        1
        for _, r in labeled.iterrows()
        if r["Expected Level"] == "danger" and r["Pred Level"] in ("safe", "caution")
    )

    per_level_recall = {}
    for lv in LEVELS:
        lv_rows = labeled[labeled["Expected Level"] == lv]
        if len(lv_rows):
            per_level_recall[lv] = (lv_rows["Pred Level"] == lv).mean()
        else:
            per_level_recall[lv] = None

    return {
        "labeled": n,
        "accuracy": correct / n,
        "per_level_recall": per_level_recall,
        "confusion": confusion,
        "under_warn_rate": under / n,
        "over_warn_rate": over / n,
        "danger_underwarn_rate": (danger_underwarn / danger_total) if danger_total else None,
        "danger_total": danger_total,
    }


def cost_for_row(row: dict[str, Any]) -> float:
    model = str(row.get("Model", ""))
    price = PRICING.get(model, {"input": 0.0, "output": 0.0})
    in_tok = float(row.get("Prompt Tokens", 0) or 0)
    out_tok = float(row.get("Output Tokens", 0) or 0)
    search = float(row.get("Search Queries", 0) or 0)
    return (
        in_tok / 1e6 * price["input"]
        + out_tok / 1e6 * price["output"]
        + search * SEARCH_COST_PER_QUERY
    )


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="상호작용 분석 결과 평가.")
    parser.add_argument("--results", default="data/result/interaction_results.xlsx")
    parser.add_argument("--scenarios", default="data/interaction_scenarios.json")
    parser.add_argument("--output", default="data/result/interaction_eval.xlsx")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--judge-provider", default="auto", choices=["auto", "gemini", "claude"])
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-judge", action="store_true", help="judge 생략, 정확도/비용만")
    parser.add_argument("--monthly-requests", type=int, default=3000,
                        help="월 예상비용 산출용 가정 요청 수")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(resolve_project_path(args.env_file))

    results_path = resolve_project_path(args.results)
    scenarios_path = resolve_project_path(args.scenarios)
    output_path = resolve_project_path(args.output)

    if not results_path.exists():
        print(f"결과 파일 없음: {results_path}", file=sys.stderr)
        return 1

    df = pd.read_excel(results_path).fillna("")
    scenarios = {
        sc["id"]: sc
        for sc in json.loads(scenarios_path.read_text(encoding="utf-8"))
    }
    if args.limit:
        df = df.head(args.limit).copy()

    # judge provider 결정
    gemini_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    provider = args.judge_provider
    if provider == "auto":
        provider = "claude" if anthropic_key else "gemini"
    judge_id = (
        f"claude:{args.judge_model}" if provider == "claude" else f"gemini:{args.judge_model}"
    )

    # ── LLM-as-judge ──
    judge_cols = [
        "Judge Factuality",
        "Judge Readability",
        "Judge Usefulness",
        "Judge Schema",
        "Judge Avg",
        "Jargon Terms",
        "Judge Rationale",
    ]
    for c in judge_cols:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].astype(object)  # 정수 점수 할당 시 str dtype 충돌 방지

    if not args.skip_judge:
        if provider == "claude" and not anthropic_key:
            print("ANTHROPIC_API_KEY 없음", file=sys.stderr)
            return 1
        if provider == "gemini" and not gemini_key:
            print("Gemini 키 없음", file=sys.stderr)
            return 1
        log(f"LLM-as-judge 시작 (judge={judge_id}, {len(df)}행)")
        for i, row in df.iterrows():
            sid = str(row.get("Scenario ID", ""))
            if str(row.get("Error", "")).strip() or not str(row.get("Pred Level", "")).strip():
                continue
            scenario = scenarios.get(sid)
            if not scenario:
                continue
            # insufficient_evidence(정답 라벨 없음)은 평가 범위 밖 → judge 생략
            if not scenario.get("expected_level"):
                continue
            candidate = row_to_candidate(row.to_dict())
            prompt = build_judge_prompt(scenario, candidate)
            try:
                if provider == "claude":
                    verdict = call_claude_judge(args.judge_model, anthropic_key, prompt)
                else:
                    verdict = call_gemini_judge(
                        args.api_base, args.judge_model, gemini_key, prompt
                    )
                scores = verdict.get("scores", {})
                vals = [scores.get(k) for k in ("factuality", "readability", "usefulness", "schema")]
                nums = [float(v) for v in vals if isinstance(v, (int, float))]
                df.at[i, "Judge Factuality"] = scores.get("factuality", "")
                df.at[i, "Judge Readability"] = scores.get("readability", "")
                df.at[i, "Judge Usefulness"] = scores.get("usefulness", "")
                df.at[i, "Judge Schema"] = scores.get("schema", "")
                df.at[i, "Judge Avg"] = round(sum(nums) / len(nums), 2) if nums else ""
                df.at[i, "Jargon Terms"] = " | ".join(verdict.get("jargon_terms_found") or [])
                df.at[i, "Judge Rationale"] = verdict.get("rationale", "")
            except Exception as exc:  # noqa: BLE001
                df.at[i, "Judge Rationale"] = f"JUDGE_ERROR: {exc}"
                log(f"  judge 실패 {sid}/{row.get('Source')}: {exc}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(output_path, index=False)
    else:
        log("judge 생략 (--skip-judge)")

    # expected_level / note를 시나리오에서 df에 보강(라벨이 결과에 안 들어간 경우)
    for i, row in df.iterrows():
        if not str(row.get("Expected Level", "")).strip():
            sc = scenarios.get(str(row.get("Scenario ID", "")))
            if sc and sc.get("expected_level"):
                df.at[i, "Expected Level"] = sc["expected_level"]

    df["__cost"] = [cost_for_row(r) for _, r in df.iterrows()]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["__cost"], errors="ignore").to_excel(output_path, index=False)
    log(f"평가 결과 저장: {output_path}")

    # ── 방식별 매트릭스 출력 ──
    print("\n" + "=" * 78)
    print(f"방식별 평가 매트릭스 (judge={judge_id if not args.skip_judge else '생략'})")
    print("=" * 78)
    for source in sorted(df["Source"].unique()):
        sub = df[df["Source"] == source]
        valid = sub[sub["Error"].astype(str).str.strip() == ""]
        m = level_metrics(valid)
        judge_avgs = pd.to_numeric(valid["Judge Avg"], errors="coerce").dropna()
        read_avgs = pd.to_numeric(valid["Judge Readability"], errors="coerce").dropna()
        total_cost = sub["__cost"].sum()
        n_req = len(valid)
        avg_cost = total_cost / n_req if n_req else 0
        monthly = avg_cost * args.monthly_requests
        avg_lat = pd.to_numeric(valid["Latency (s)"], errors="coerce").dropna().mean()
        avg_in = pd.to_numeric(valid["Prompt Tokens"], errors="coerce").dropna().mean()
        avg_out = pd.to_numeric(valid["Output Tokens"], errors="coerce").dropna().mean()

        print(f"\n[ {source} ]  (행 {len(sub)}, 유효 {n_req})")
        if m.get("labeled"):
            print(f"  레벨 정확도: {m['accuracy']:.1%} (라벨 {m['labeled']})")
            print(f"  레벨별 recall: " + ", ".join(
                f"{lv}={('%.0f%%' % (v*100)) if v is not None else 'N/A'}"
                for lv, v in m["per_level_recall"].items()
            ))
            duw = m["danger_underwarn_rate"]
            print(f"  과소경고율(전체): {m['under_warn_rate']:.1%} | "
                  f"danger 과소경고율: {('%.1f%%' % (duw*100)) if duw is not None else 'N/A'} "
                  f"(danger {m['danger_total']}건)")
            print(f"  과대경고율: {m['over_warn_rate']:.1%}")
            print("  혼동행렬(행=정답, 열=예측): " + json.dumps(m["confusion"], ensure_ascii=False))
        else:
            print("  레벨 정확도: 라벨된 시나리오 없음(expected_level 미입력)")
        if len(judge_avgs):
            print(f"  judge 평균: {judge_avgs.mean():.2f}/5 | 가독성: {read_avgs.mean():.2f}/5")
        print(f"  평균 지연: {avg_lat:.1f}s | 평균 토큰 in/out: {avg_in:.0f}/{avg_out:.0f}")
        print(f"  쿼리당 비용: ${avg_cost:.5f} | 월 예상비용(@{args.monthly_requests}req): ${monthly:.2f}")
        # JSON Mode 분포
        mode_dist = sub["JSON Mode"].value_counts().to_dict()
        print(f"  JSON Mode 분포: {mode_dist}")

    print("\n" + "=" * 78)
    print("※ 비용 단가(PRICING)는 placeholder — 게시 요율로 갱신 후 재실행 권장.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
