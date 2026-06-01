from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


EXPECTED_COLUMNS = [
    "Index",
    "File Path",
    "Product Name",
    "Anchor YN",
    "OCR Text",
    "OCR Result",
    "VLM Text",
    "VLM Result",
    "API Text",
    "API Result",
    "API 2 Text",
    "API 2 Result",
]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

NUTRITION_PROMPT_TEXT = (
    "다음 텍스트에서 영양성분과 그 함량(절대량)만 추출하세요.\n"
    "규칙:\n"
    "- 한 줄에 영양성분 1개씩\n"
    "- 형식: 성분명 함량 (예: 비타민C 1000mg, 루테인 20mg)\n"
    "- 절대 함량(mg, μg, g, IU 등 실제 양)만 포함\n"
    "- 비율(%)은 모두 제외 (1일 영양성분기준치 %, 함량 옆에 괄호로 적힌 % 등)\n"
    "- 숫자 사이 천 단위 쉼표는 제거 (예: '1,000' → '1000', '4,917' → '4917')\n"
    "- 영양성분/기능성분/지표성분만 포함, 다른 텍스트(브랜드, 제조사, 주의사항, 보관방법 등)는 모두 무시\n"
    "- 함량이 0인 항목(예: 열량 0kcal, 단백질 0g, 지방 0g, 탄수화물 0g, 나트륨 0mg)은 제외\n"
    "- 설명, 머리말, 마무리, 마크다운, 코드블록, JSON 사용 금지\n"
    "- 정렬은 텍스트에 나온 순서대로\n\n"
    "텍스트:\n{text}"
)

NUTRITION_PROMPT_IMAGE = (
    "이 이미지에서 영양성분과 그 함량(절대량)만 추출하세요.\n"
    "규칙:\n"
    "- 한 줄에 영양성분 1개씩\n"
    "- 형식: 성분명 함량 (예: 비타민C 1000mg, 루테인 20mg)\n"
    "- 절대 함량(mg, μg, g, IU 등 실제 양)만 포함\n"
    "- 비율(%)은 모두 제외 (1일 영양성분기준치 %, 함량 옆에 괄호로 적힌 % 등)\n"
    "- 숫자 사이 천 단위 쉼표는 제거 (예: '1,000' → '1000', '4,917' → '4917')\n"
    "- 영양성분/기능성분/지표성분만 포함, 다른 텍스트(브랜드, 제조사, 주의사항, 보관방법 등)는 모두 무시\n"
    "- 함량이 0인 항목(예: 열량 0kcal, 단백질 0g, 지방 0g, 탄수화물 0g, 나트륨 0mg)은 제외\n"
    "- 설명, 머리말, 마무리, 마크다운, 코드블록, JSON 사용 금지\n"
    "- 이미지에 영양성분 정보가 없으면 빈 응답 대신 'NONE' 한 단어만 출력"
)

MAX_ATTEMPTS = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract nutrition facts from images and ground truth via Gemini, "
            "then score image-side extraction against ground-truth-side extraction. "
            "Writes API 2 Text and API 2 Result columns."
        )
    )
    parser.add_argument("--data-dir", default="data/영양제")
    parser.add_argument("--input", default="data/result/nutri_results.xlsx")
    parser.add_argument(
        "--gt-cache",
        default="data/result/nutrition_gt_cache.json",
        help="Per-product ground truth nutrition extraction cache.",
    )
    parser.add_argument(
        "--img-cache",
        default="data/result/nutrition_image_cache.json",
        help="Per-product image nutrition extraction cache (one anchor image per product).",
    )
    parser.add_argument("--api-model", default="gemini-3.1-flash-lite")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument(
        "--api-base", default="https://generativelanguage.googleapis.com/v1beta"
    )
    parser.add_argument("--request-interval", type=float, default=4.5)
    parser.add_argument("--force", action="store_true", help="Re-extract every image.")
    parser.add_argument(
        "--force-gt",
        action="store_true",
        help="Re-extract ground truth nutrition (clears cache).",
    )
    return parser.parse_args()


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


def load_ground_truth_text(data_dir: Path, product_name: str) -> str:
    txt_path = data_dir / f"{product_name}.txt"
    if not txt_path.exists():
        return ""
    return txt_path.read_text(encoding="utf-8").strip()


def strip_digit_commas(text: str) -> str:
    return re.sub(r"(?<=\d),(?=\d)", "", text)


def calculate_match_score(gt_nutrition: str, cand_nutrition: str) -> str:
    """Option A scoring: GT whitespace-tokens, substring-checked in cand with whitespace removed.
    Both sides are also stripped of comma thousand-separators."""
    gt_clean = strip_digit_commas(gt_nutrition.lower())
    cand_clean = strip_digit_commas(cand_nutrition.lower())
    gt_tokens = [t for t in gt_clean.split() if t.strip()]
    if not gt_tokens:
        return "N/A"
    cand_nospace = "".join(cand_clean.split())
    matched = sum(1 for tok in gt_tokens if tok in cand_nospace)
    score = matched / len(gt_tokens)
    return f"{score:.2%} ({matched}/{len(gt_tokens)})"


def encode_image_to_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def detect_mime_type(image_path: Path) -> str:
    return MIME_TYPES.get(image_path.suffix.lower(), "image/png")


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
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


def gemini_call(
    api_base: str,
    model_name: str,
    api_key: str,
    parts: list[dict],
) -> str:
    url = f"{api_base}/models/{model_name}:generateContent"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 1024},
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
            log(f"      ⏳ network error (attempt {attempt + 1}/{MAX_ATTEMPTS}): {exc}. Sleeping {wait:.1f}s...")
            time.sleep(wait)
            continue

        if response.status_code == 429:
            quota_labels, retry_delay = parse_429_quota(response.text)
            quota_str = ", ".join(quota_labels) if quota_labels else "unknown"
            retry_header = response.headers.get("Retry-After")
            retry_seconds = parse_duration_seconds(retry_delay) or parse_duration_seconds(retry_header)
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
            last_error = ValueError(f"429 quota hit ({quota_str})")
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            wait = 2 ** attempt * 5
            log(f"      ⏳ {response.status_code} server error (attempt {attempt + 1}/{MAX_ATTEMPTS}). Sleeping {wait:.1f}s...")
            last_error = ValueError(f"{response.status_code} server error: {response.text[:200]}")
            time.sleep(wait)
            continue

        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            block = (data.get("promptFeedback") or {}).get("blockReason")
            raise ValueError(f"No candidates returned. blockReason={block}, payload={data}")
        candidate = candidates[0]
        content = candidate.get("content") or {}
        parts_out = content.get("parts") or []
        text = "".join(part.get("text", "") for part in parts_out).strip()
        if not text:
            raise ValueError(
                f"Empty Gemini response. finishReason={candidate.get('finishReason')}, payload={data}"
            )
        return clean_output(text)

    raise RuntimeError(f"Gemini request failed after retries: {last_error}")


def clean_output(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", s)
        if s.endswith("```"):
            s = s[: -len("```")]
        s = s.strip()
    return s


def extract_gt_nutrition(
    api_base: str, model_name: str, api_key: str, gt_text: str
) -> str:
    prompt = NUTRITION_PROMPT_TEXT.format(text=gt_text)
    return gemini_call(api_base, model_name, api_key, [{"text": prompt}])


def extract_image_nutrition(
    api_base: str, model_name: str, api_key: str, image_path: Path
) -> str:
    parts = [
        {"text": NUTRITION_PROMPT_IMAGE},
        {
            "inline_data": {
                "mime_type": detect_mime_type(image_path),
                "data": encode_image_to_base64(image_path),
            }
        },
    ]
    return gemini_call(api_base, model_name, api_key, parts)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("API 2 Text", "API 2 Result"):
        if col not in df.columns:
            df[col] = ""
    df["API 2 Text"] = df["API 2 Text"].astype(str)
    df["API 2 Result"] = df["API 2 Result"].astype(str)
    ordered = [col for col in EXPECTED_COLUMNS if col in df.columns]
    remaining = [col for col in df.columns if col not in ordered]
    return df[ordered + remaining]


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)


def load_gt_cache(cache_path: Path) -> dict[str, str]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_gt_cache(cache_path: Path, cache: dict[str, str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir)
    input_path = Path(args.input)
    cache_path = Path(args.gt_cache)

    load_env_file(Path(args.env_file))
    api_key = (
        args.api_key
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not api_key:
        print(
            "Missing Gemini API key. Pass --api-key, set GOOGLE_API_KEY / GEMINI_API_KEY, "
            f"or add it to {args.env_file}.",
            file=sys.stderr,
        )
        return 1

    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1
    if not input_path.exists():
        print(f"Excel input not found: {input_path}", file=sys.stderr)
        return 1

    log(f"Loading Excel: {input_path}")
    df = pd.read_excel(input_path).fillna("")
    df = ensure_columns(df)

    gt_cache = {} if args.force_gt else load_gt_cache(cache_path)
    log(f"GT cache: {len(gt_cache)} product(s) loaded from {cache_path}")

    products: dict[str, list[int]] = defaultdict(list)
    for idx in df.index:
        product_name = str(df.at[idx, "Product Name"]).strip()
        if product_name:
            products[product_name].append(idx)

    def is_pending(i: int) -> bool:
        if args.force:
            return True
        text = str(df.at[i, "API 2 Text"])
        result = str(df.at[i, "API 2 Result"])
        if not text.strip() or not result.strip():
            return True
        if text.startswith("ERROR:") or result == "ERROR":
            return True
        return False

    total = len(df)
    pending_total = sum(
        1 for indices in products.values() for i in indices if is_pending(i)
    )
    log(
        f"Loaded {total} rows across {len(products)} products. "
        f"Pending: {pending_total}, already filled: {total - pending_total}."
    )
    log(f"Using Gemini model: {args.api_model}")
    log(f"Request interval: {args.request_interval}s")

    overall_start = time.monotonic()
    processed = 0
    requests_sent = 0
    for product_idx, (product_name, indices) in enumerate(products.items(), start=1):
        pending = [i for i in indices if is_pending(i)]
        if not pending:
            log(
                f"[product {product_idx}/{len(products)}] {product_name} | "
                f"all {len(indices)} row(s) already filled, skipping"
            )
            processed += len(indices)
            continue

        if product_name not in gt_cache:
            gt_text = load_ground_truth_text(data_dir, product_name)
            if not gt_text:
                log(f"[product {product_idx}/{len(products)}] {product_name} | GT MISSING, skipping product")
                processed += len(indices)
                continue
            if requests_sent > 0 and args.request_interval > 0:
                time.sleep(args.request_interval)
            log(f"[product {product_idx}/{len(products)}] {product_name} | extracting GT nutrition...")
            gt_start = time.monotonic()
            try:
                gt_nutrition = extract_gt_nutrition(
                    args.api_base, args.api_model, api_key, gt_text
                )
                gt_cache[product_name] = gt_nutrition
                save_gt_cache(cache_path, gt_cache)
                elapsed = time.monotonic() - gt_start
                log(f"  ↳ GT extracted ({elapsed:.1f}s, {len(gt_nutrition)} chars)")
                log(f"    GT nutrition:\n{gt_nutrition}")
            except Exception as exc:
                elapsed = time.monotonic() - gt_start
                log(f"  ✗ GT extraction ERROR after {elapsed:.1f}s: {exc}")
                for i in indices:
                    df.at[i, "API 2 Text"] = f"ERROR: GT extraction failed: {exc}"
                    df.at[i, "API 2 Result"] = "ERROR"
                processed += len(indices)
                save_dataframe(df, input_path)
                requests_sent += 1
                continue
            requests_sent += 1

        gt_nutrition = gt_cache[product_name]
        log(
            f"[product {product_idx}/{len(products)}] {product_name} | "
            f"{len(pending)} image(s) pending"
        )
        for image_idx, i in enumerate(pending, start=1):
            image_path = Path(str(df.at[i, "File Path"]))
            file_name = image_path.name
            if requests_sent > 0 and args.request_interval > 0:
                time.sleep(args.request_interval)
            log(f"    → [{image_idx}/{len(pending)}] {file_name} ... extracting nutrition")
            image_start = time.monotonic()
            try:
                img_nutrition = extract_image_nutrition(
                    args.api_base, args.api_model, api_key, image_path
                )
                score = calculate_match_score(gt_nutrition, img_nutrition)
                df.at[i, "API 2 Text"] = img_nutrition
                df.at[i, "API 2 Result"] = score
                elapsed = time.monotonic() - image_start
                log(
                    f"    ✓ [{image_idx}/{len(pending)}] {file_name} "
                    f"→ {score} ({elapsed:.1f}s, {len(img_nutrition)} chars)"
                )
            except Exception as exc:
                elapsed = time.monotonic() - image_start
                df.at[i, "API 2 Text"] = f"ERROR: {exc}"
                df.at[i, "API 2 Result"] = "ERROR"
                log(
                    f"    ✗ [{image_idx}/{len(pending)}] {file_name} "
                    f"→ ERROR after {elapsed:.1f}s: {exc}"
                )
            requests_sent += 1
            save_dataframe(df, input_path)

        processed += len(indices)
        save_dataframe(df, input_path)
        log(f"  ↳ saved checkpoint ({processed}/{total} rows)")

    save_dataframe(df, input_path)
    total_elapsed = time.monotonic() - overall_start
    log(f"Done in {total_elapsed:.1f}s. Saved: {input_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
