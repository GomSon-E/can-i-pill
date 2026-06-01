from __future__ import annotations

import argparse
import base64
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
EXPECTED_COLUMNS = [
    "Index",
    "File Path",
    "OCR Text",
    "OCR Result",
    "VLM Text",
    "VLM Result",
    "API Text",
    "API Result",
]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

TOKEN_PATTERN = re.compile(r"[0-9A-Za-z가-힣.%]+")
# 채점 규칙: 정답 토큰 집계 시 제외/정규화할 키
EXCLUDED_TOP_LEVEL_KEYS = {"처방전", "질환명", "질병분류기호"}
UNIT_STRIPPED_KEYS = {"1회투약량"}

PRESCRIPTION_PROMPT_IMAGE = (
    "이 처방전 이미지에서 처방의약품 관련 정보만 추출하세요.\n"
    "규칙:\n"
    "- 질환명, 질병분류기호, 각 의약품의 약품명, 1회투약량, 1일투여횟수, 총투약일수, 용법, 주의사항만 추출\n"
    "- 병원명, 주소, 전화번호, 환자 개인정보, 서명란, 약국사용란, 일반 안내문구는 제외\n"
    "- 약품별 정보는 한 덩어리로 묶어서 줄바꿈으로 구분\n"
    "- 약품명은 보이는 한글/영문/용량 표기를 가능한 그대로 유지\n"
    "- 설명, 요약, 해석, 마크다운, 코드블록, JSON 금지\n"
    "- 읽히지 않는 부분은 추측하지 말고 생략\n"
    "- 처방의약품 정보가 전혀 없으면 NONE 한 단어만 출력\n"
    "- 오직 추출된 텍스트만 출력\n"
    "\n"
    "출력 예시:\n"
    "질환명: 고혈압\n"
    "질병분류기호: I10\n"
    "약품명: 암로디핀정 5mg\n"
    "1회투약량: 1정\n"
    "1일투여횟수: 1\n"
    "총투약일수: 30\n"
    "용법: 아침 식후 30분\n"
    "주의사항: 발목 부종, 두통 발생 시 의사 상담\n"
    "\n"
    "약품명: 텔미사르탄정 40mg\n"
    "1회투약량: 1정\n"
    "1일투여횟수: 1\n"
    "총투약일수: 30\n"
    "용법: 아침 식후 30분"
)

MAX_ATTEMPTS = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract prescription text from images via the Google Gemini API and "
            "fill the API Text / API Result columns in the prescription Excel file."
        )
    )
    parser.add_argument("--data-dir", default="data/처방전")
    parser.add_argument("--input", default="data/result/rx_results.xlsx")
    parser.add_argument(
        "--gt-json",
        default="data/처방전/text.json",
        help="Ground truth prescription JSON used for API scoring.",
    )
    parser.add_argument("--api-model", default="gemini-3.1-flash-lite")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument(
        "--api-base", default="https://generativelanguage.googleapis.com/v1beta"
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=4.5,
        help="Seconds to wait between requests to stay under free-tier RPM limits.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run for every row, overwriting any existing API Text/Result values.",
    )
    return parser.parse_args()


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


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


def normalize_prescription_name(name: str) -> str:
    return re.sub(r"[\s_]+", "", name).lower()


def load_answer_map(text_json_path: Path) -> dict[str, set[str]]:
    if not text_json_path.exists():
        return {}

    payload = json.loads(text_json_path.read_text(encoding="utf-8"))
    answer_map: dict[str, set[str]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        prescription_name = str(item.get("처방전", "")).strip()
        if not prescription_name:
            continue
        key = normalize_prescription_name(prescription_name)
        answer_map[key] = extract_answer_tokens(item)
    return answer_map


def strip_dose_unit(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    match = re.match(r"^([\d.]+)", text)
    if match:
        return match.group(1)
    return text


def extract_answer_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()

    def walk(node: Any, depth: int = 0) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            for key, child in node.items():
                if depth == 0 and key in EXCLUDED_TOP_LEVEL_KEYS:
                    continue
                if key in UNIT_STRIPPED_KEYS:
                    child = strip_dose_unit(child)
                walk(child, depth + 1)
            return
        if isinstance(node, list):
            for child in node:
                walk(child, depth + 1)
            return

        text = str(node).strip()
        if not text:
            return

        for token in TOKEN_PATTERN.findall(text):
            normalized = normalize_token(token)
            if normalized:
                tokens.add(normalized)

    walk(value)
    return tokens


def normalize_token(token: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", token.lower())


def calculate_match_score(file_path: Path, extracted_text: str, answer_map: dict[str, set[str]]) -> str:
    key = normalize_prescription_name(file_path.stem)
    answer_tokens = answer_map.get(key)
    if not answer_tokens:
        return "N/A"

    extracted_tokens = {
        normalized
        for token in TOKEN_PATTERN.findall(extracted_text)
        for normalized in [normalize_token(token)]
        if normalized
    }
    matched_count = sum(1 for token in answer_tokens if token in extracted_tokens)
    total_count = len(answer_tokens)
    score = matched_count / total_count if total_count else 0
    return f"{score:.2%} ({matched_count}/{total_count})"


def encode_image_to_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def detect_mime_type(image_path: Path) -> str:
    return MIME_TYPES.get(image_path.suffix.lower(), "image/png")


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def classify_quota_id(quota_id: str) -> str:
    qid = quota_id.lower()
    if "perday" in qid:
        return "RPD (per day)"
    if "tokens" in qid and "perminute" in qid:
        return "TPM (tokens per minute)"
    if "perminute" in qid:
        return "RPM (per minute)"
    return f"unknown ({quota_id})"


def parse_429_quota(response_text: str) -> tuple[list[str], str | None]:
    quota_labels: list[str] = []
    retry_delay: str | None = None
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return quota_labels, retry_delay
    error = data.get("error") or {}
    for detail in error.get("details", []):
        dtype = detail.get("@type", "")
        if dtype.endswith("QuotaFailure"):
            for violation in detail.get("violations", []):
                quota_id = violation.get("quotaId") or violation.get("quotaMetric") or ""
                if quota_id:
                    quota_labels.append(classify_quota_id(quota_id))
        elif dtype.endswith("RetryInfo"):
            retry_delay = detail.get("retryDelay")
    return quota_labels, retry_delay


def parse_duration_seconds(value: str | None) -> float | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("s"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


def clean_output(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
        cleaned = cleaned.strip()
    return cleaned


def call_gemini(
    api_base: str,
    model_name: str,
    api_key: str,
    image_path: Path,
) -> str:
    url = f"{api_base}/models/{model_name}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PRESCRIPTION_PROMPT_IMAGE},
                    {
                        "inline_data": {
                            "mime_type": detect_mime_type(image_path),
                            "data": encode_image_to_base64(image_path),
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 2048,
        },
    }

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.post(
                url, params={"key": api_key}, json=payload, timeout=120
            )
        except requests.RequestException as exc:
            last_error = exc
            wait = 2 ** attempt * 2
            log(
                f"      ⏳ network error (attempt {attempt + 1}/{MAX_ATTEMPTS}): "
                f"{exc}. Sleeping {wait:.1f}s before retry..."
            )
            time.sleep(wait)
            continue

        if response.status_code == 429:
            quota_labels, retry_delay = parse_429_quota(response.text)
            quota_str = ", ".join(quota_labels) if quota_labels else "unknown"
            retry_header = response.headers.get("Retry-After")
            retry_seconds = parse_duration_seconds(retry_delay) or parse_duration_seconds(
                retry_header
            )
            retry_display = retry_delay or retry_header or "none"
            if retry_seconds is None:
                wait = 2 ** attempt * 10
                source = "exponential backoff"
            else:
                wait = retry_seconds + 1.0
                source = "API hint"

            log(
                f"      ⏳ 429 quota hit: {quota_str} "
                f"(attempt {attempt + 1}/{MAX_ATTEMPTS}, Retry-After={retry_display}). "
                f"Sleeping {wait:.1f}s ({wait / 60:.1f}m) via {source}..."
            )
            last_error = ValueError(
                f"429 quota hit ({quota_str}) after {attempt + 1} attempts"
            )
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            wait = 2 ** attempt * 5
            log(
                f"      ⏳ {response.status_code} server error "
                f"(attempt {attempt + 1}/{MAX_ATTEMPTS}). "
                f"Sleeping {wait:.1f}s before retry..."
            )
            last_error = ValueError(
                f"{response.status_code} server error: {response.text[:200]}"
            )
            time.sleep(wait)
            continue

        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            block_reason = (data.get("promptFeedback") or {}).get("blockReason")
            raise ValueError(
                f"No candidates returned. blockReason={block_reason}, payload={data}"
            )

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()

        if not text:
            raise ValueError(
                f"Empty Gemini response. finishReason={finish_reason}, payload={data}"
            )
        return clean_output(text)

    raise RuntimeError(f"Gemini request failed after retries: {last_error}")


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("API Text", "API Result"):
        if col not in df.columns:
            df[col] = ""
    df["API Text"] = df["API Text"].astype(str)
    df["API Result"] = df["API Result"].astype(str)

    ordered = [col for col in EXPECTED_COLUMNS if col in df.columns]
    remaining = [col for col in df.columns if col not in ordered]
    return df[ordered + remaining]


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    df.to_excel(output_path, index=False)


def main() -> int:
    args = parse_args()
    data_dir = resolve_project_path(args.data_dir)
    input_path = resolve_project_path(args.input)
    gt_json_path = resolve_project_path(args.gt_json)

    load_env_file(resolve_project_path(args.env_file))

    api_key = (
        args.api_key
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not api_key:
        print(
            "Missing Gemini API key. Pass --api-key, set GOOGLE_API_KEY / GEMINI_API_KEY, "
            f"or add it to {args.env_file}.\n"
            "Get a key at https://aistudio.google.com/apikey",
            file=sys.stderr,
        )
        return 1

    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1
    if not input_path.exists():
        print(f"Excel input not found: {input_path}", file=sys.stderr)
        return 1
    if not gt_json_path.exists():
        print(f"Ground truth JSON not found: {gt_json_path}", file=sys.stderr)
        return 1

    log(f"Loading ground truth JSON: {gt_json_path}")
    answer_map = load_answer_map(gt_json_path)
    log(f"Ground truth entries: {len(answer_map)}")

    log(f"Loading Excel: {input_path}")
    df = pd.read_excel(input_path).fillna("")
    df = ensure_columns(df)

    def is_pending(i: int) -> bool:
        if args.force:
            return True
        api_text = str(df.at[i, "API Text"])
        api_result = str(df.at[i, "API Result"])
        if not api_text.strip() or not api_result.strip():
            return True
        if api_text.startswith("ERROR:") or api_result == "ERROR":
            return True
        return False

    total = len(df)
    pending_indices = [i for i in df.index if is_pending(i)]
    log(
        f"Loaded {total} row(s). API pending: {len(pending_indices)}, "
        f"already filled: {total - len(pending_indices)}."
    )
    log(f"Using Gemini model: {args.api_model}")
    log(
        f"Request interval: {args.request_interval}s "
        f"(≈ {60 / max(args.request_interval, 0.1):.1f} RPM)"
    )
    log(f"Started API export for {len(pending_indices)} image(s).")

    overall_start = time.monotonic()
    requests_sent = 0
    for image_idx, i in enumerate(pending_indices, start=1):
        image_path = Path(str(df.at[i, "File Path"])).resolve()
        file_name = image_path.name
        if requests_sent > 0 and args.request_interval > 0:
            time.sleep(args.request_interval)
        log(f"[API {image_idx}/{len(pending_indices)}] Starting image: {file_name}")
        image_start = time.monotonic()
        try:
            api_text = call_gemini(
                args.api_base, args.api_model, api_key, image_path
            )
            score = calculate_match_score(image_path, api_text, answer_map)
            df.at[i, "API Text"] = api_text
            df.at[i, "API Result"] = score
            elapsed = time.monotonic() - image_start
            log(
                f"[API {image_idx}/{len(pending_indices)}] Finished image: "
                f"{file_name} | API Result: {score} ({elapsed:.1f}s, {len(api_text)} chars)"
            )
        except Exception as exc:
            elapsed = time.monotonic() - image_start
            df.at[i, "API Text"] = f"ERROR: {exc}"
            df.at[i, "API Result"] = "ERROR"
            log(
                f"[API {image_idx}/{len(pending_indices)}] Finished image: "
                f"{file_name} | ERROR after {elapsed:.1f}s: {exc}"
            )
        requests_sent += 1
        save_dataframe(df, input_path)
        log(f"[API {image_idx}/{len(pending_indices)}] Saved Excel through: {file_name}")

    total_elapsed = time.monotonic() - overall_start
    log(f"Saved Excel file: {input_path}")
    log(f"Completed API export in {total_elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
