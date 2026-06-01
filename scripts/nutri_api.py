from __future__ import annotations

import argparse
import base64
import difflib
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
]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read an existing nutri_results.xlsx, send each image to the Google "
            "Gemini API, and fill the API Text and API Result columns. OCR/VLM columns "
            "are left untouched."
        )
    )
    parser.add_argument(
        "--data-dir",
        default="data/영양제",
        help="Directory containing source images and {product_name}.txt ground truth files.",
    )
    parser.add_argument(
        "--input",
        default="data/result/nutri_results.xlsx",
        help="Excel input/output path. The file is updated in place.",
    )
    parser.add_argument(
        "--api-model",
        default="gemini-3.1-flash-lite",
        help="Gemini model name (e.g. gemini-3.1-flash-lite, gemini-2.5-flash-lite, gemini-2.5-flash).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Gemini API key. If omitted, reads GOOGLE_API_KEY or GEMINI_API_KEY (from --env-file or environment).",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file. Loaded before reading API key env vars.",
    )
    parser.add_argument(
        "--api-base",
        default="https://generativelanguage.googleapis.com/v1beta",
        help="Gemini API base URL.",
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=4.5,
        help="Seconds to wait between requests to stay under free-tier RPM limits "
        "(gemini-2.5-flash-lite free tier ≈ 15 RPM).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run for every row, overwriting any existing API Text/Result values.",
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


def normalize_for_comparison(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^0-9a-z가-힣]+", "", normalized)
    return normalized


def calculate_match_score(ground_truth_text: str, candidate_text: str) -> str:
    ground_truth_normalized = normalize_for_comparison(ground_truth_text)
    candidate_normalized = normalize_for_comparison(candidate_text)

    if not ground_truth_normalized:
        return "N/A"

    matcher = difflib.SequenceMatcher(a=ground_truth_normalized, b=candidate_normalized)
    matched_chars = sum(block.size for block in matcher.get_matching_blocks())
    total_chars = len(ground_truth_normalized)
    score = matched_chars / total_chars
    return f"{score:.2%} ({matched_chars}/{total_chars})"


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
    if "perdaytokens" in qid or ("perday" in qid and "token" in qid):
        return "TPD (tokens per day)"
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


MAX_ATTEMPTS = 8


def call_gemini(
    api_base: str,
    model_name: str,
    api_key: str,
    image_path: Path,
) -> str:
    prompt = (
        "이 이미지에 보이는 모든 글자를 그대로 추출하세요. "
        "설명, 해석, 요약, 머리말, 마무리 문장 없이 오직 추출한 텍스트만 출력하세요. "
        "줄바꿈은 자유롭게 사용 가능합니다."
    )
    url = f"{api_base}/models/{model_name}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
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
            "maxOutputTokens": 1024,
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
        return text

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
    data_dir = Path(args.data_dir)
    input_path = Path(args.input)

    load_env_file(Path(args.env_file))

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

    log(f"Loading Excel: {input_path}")
    df = pd.read_excel(input_path).fillna("")
    df = ensure_columns(df)

    products: dict[str, list[int]] = defaultdict(list)
    for idx in df.index:
        product_name = str(df.at[idx, "Product Name"]).strip()
        if product_name:
            products[product_name].append(idx)

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
    pending_total = sum(
        1 for indices in products.values() for i in indices if is_pending(i)
    )
    log(
        f"Loaded {total} rows across {len(products)} products. "
        f"API pending: {pending_total}, already filled: {total - pending_total}."
    )
    log(f"Using Gemini model: {args.api_model}")
    log(
        f"Request interval: {args.request_interval}s "
        f"(≈ {60 / max(args.request_interval, 0.1):.1f} RPM)"
    )

    overall_start = time.monotonic()
    processed = 0
    requests_sent = 0
    for product_idx, (product_name, indices) in enumerate(products.items(), start=1):
        pending = [i for i in indices if is_pending(i)]
        ground_truth_text = load_ground_truth_text(data_dir, product_name)
        gt_status = (
            f"{len(ground_truth_text)} chars" if ground_truth_text else "MISSING"
        )
        if pending:
            log(
                f"[product {product_idx}/{len(products)}] {product_name} | "
                f"{len(pending)} image(s) pending | ground truth: {gt_status}"
            )
            for image_idx, i in enumerate(pending, start=1):
                image_path = Path(str(df.at[i, "File Path"]))
                file_name = image_path.name
                if requests_sent > 0 and args.request_interval > 0:
                    time.sleep(args.request_interval)
                log(f"    → [{image_idx}/{len(pending)}] {file_name} ... calling Gemini")
                image_start = time.monotonic()
                try:
                    api_text = call_gemini(
                        args.api_base, args.api_model, api_key, image_path
                    )
                    score = calculate_match_score(ground_truth_text, api_text)
                    df.at[i, "API Text"] = api_text
                    df.at[i, "API Result"] = score
                    elapsed = time.monotonic() - image_start
                    log(
                        f"    ✓ [{image_idx}/{len(pending)}] {file_name} "
                        f"→ {score} ({elapsed:.1f}s, {len(api_text)} chars)"
                    )
                except Exception as exc:
                    elapsed = time.monotonic() - image_start
                    df.at[i, "API Text"] = f"ERROR: {exc}"
                    df.at[i, "API Result"] = "ERROR"
                    log(
                        f"    ✗ [{image_idx}/{len(pending)}] {file_name} "
                        f"→ ERROR after {elapsed:.1f}s: {exc}"
                    )
                requests_sent += 1
                save_dataframe(df, input_path)
        else:
            log(
                f"[product {product_idx}/{len(products)}] {product_name} | "
                f"all {len(indices)} row(s) already filled, skipping"
            )

        processed += len(indices)
        save_dataframe(df, input_path)
        log(f"  ↳ saved checkpoint ({processed}/{total} rows)")

    save_dataframe(df, input_path)
    total_elapsed = time.monotonic() - overall_start
    log(f"Done in {total_elapsed:.1f}s. Saved: {input_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
