from __future__ import annotations

import argparse
import base64
import json
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
    "VLM 2 Text",
    "VLM 2 Result",
]

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
    "- 이미지에 영양성분 정보가 없으면 'NONE' 한 단어만 출력"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract nutrition facts from images via local VLM (Ollama) and score "
            "against the ground truth nutrition extracted by nutri_api_ingr.py. "
            "Writes VLM 2 Text and VLM 2 Result columns."
        )
    )
    parser.add_argument("--data-dir", default="data/영양제")
    parser.add_argument("--input", default="data/result/nutri_results.xlsx")
    parser.add_argument(
        "--gt-cache",
        default="data/result/nutrition_gt_cache.json",
        help="Per-product GT nutrition cache produced by nutri_api_ingr.py.",
    )
    parser.add_argument(
        "--vlm-model",
        default="qwen2.5vl:3b",
        help="Ollama VLM model name (Qwen2.5-VL 3B by default).",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://127.0.0.1:11434/api/chat",
        help="Ollama chat API URL.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract for every row, overwriting existing VLM 2 Text/Result.",
    )
    return parser.parse_args()


def load_gt_cache(cache_path: Path) -> dict[str, str]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def strip_digit_commas(text: str) -> str:
    return re.sub(r"(?<=\d),(?=\d)", "", text)


def calculate_match_score(gt_nutrition: str, cand_nutrition: str) -> str:
    """Option A: GT whitespace-tokens substring-checked in cand (whitespace removed).
    Commas between digits are stripped on both sides."""
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


def clean_output(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", s)
        if s.endswith("```"):
            s = s[: -len("```")]
        s = s.strip()
    return s


def run_vlm_nutrition(ollama_url: str, model_name: str, image_path: Path) -> str:
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": NUTRITION_PROMPT_IMAGE,
                "images": [encode_image_to_base64(image_path)],
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 1024,
        },
    }
    response = requests.post(ollama_url, json=payload, timeout=600)
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    raw_content = str(message.get("content", "")).strip()
    if not raw_content:
        raise ValueError(f"Empty VLM response. Full payload: {data}")
    return clean_output(raw_content)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("VLM 2 Text", "VLM 2 Result"):
        if col not in df.columns:
            df[col] = ""
    df["VLM 2 Text"] = df["VLM 2 Text"].astype(str)
    df["VLM 2 Result"] = df["VLM 2 Result"].astype(str)

    ordered = [col for col in EXPECTED_COLUMNS if col in df.columns]
    remaining = [col for col in df.columns if col not in ordered]
    return df[ordered + remaining]


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    df.to_excel(output_path, index=False)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir)
    input_path = Path(args.input)
    cache_path = Path(args.gt_cache)

    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1
    if not input_path.exists():
        print(f"Excel input not found: {input_path}", file=sys.stderr)
        return 1
    if not cache_path.exists():
        print(
            f"GT cache not found: {cache_path}\n"
            "Run scripts/nutri_api_ingr.py first to build the GT cache.",
            file=sys.stderr,
        )
        return 1

    log(f"Loading GT cache: {cache_path}")
    gt_cache = load_gt_cache(cache_path)
    log(f"GT cache: {len(gt_cache)} product(s)")

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
        text = str(df.at[i, "VLM 2 Text"])
        result = str(df.at[i, "VLM 2 Result"])
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
    log(f"Using VLM model: {args.vlm_model} @ {args.ollama_url}")

    overall_start = time.monotonic()
    processed = 0
    for product_idx, (product_name, indices) in enumerate(products.items(), start=1):
        pending = [i for i in indices if is_pending(i)]
        gt_nutrition = gt_cache.get(product_name, "")
        gt_status = (
            f"{len(gt_nutrition)} chars" if gt_nutrition else "MISSING in cache"
        )

        if not gt_nutrition:
            log(
                f"[product {product_idx}/{len(products)}] {product_name} | "
                f"GT cache MISSING — skipping product"
            )
            for i in indices:
                df.at[i, "VLM 2 Text"] = "ERROR: GT cache missing"
                df.at[i, "VLM 2 Result"] = "ERROR"
            processed += len(indices)
            save_dataframe(df, input_path)
            continue

        if pending:
            log(
                f"[product {product_idx}/{len(products)}] {product_name} | "
                f"{len(pending)} image(s) pending | GT: {gt_status}"
            )
            for image_idx, i in enumerate(pending, start=1):
                image_path = Path(str(df.at[i, "File Path"]))
                file_name = image_path.name
                log(f"    → [{image_idx}/{len(pending)}] {file_name} ... extracting nutrition")
                image_start = time.monotonic()
                try:
                    vlm_nutrition = run_vlm_nutrition(
                        args.ollama_url, args.vlm_model, image_path
                    )
                    score = calculate_match_score(gt_nutrition, vlm_nutrition)
                    df.at[i, "VLM 2 Text"] = vlm_nutrition
                    df.at[i, "VLM 2 Result"] = score
                    elapsed = time.monotonic() - image_start
                    log(
                        f"    ✓ [{image_idx}/{len(pending)}] {file_name} "
                        f"→ {score} ({elapsed:.1f}s, {len(vlm_nutrition)} chars)"
                    )
                except Exception as exc:
                    elapsed = time.monotonic() - image_start
                    df.at[i, "VLM 2 Text"] = f"ERROR: {exc}"
                    df.at[i, "VLM 2 Result"] = "ERROR"
                    log(
                        f"    ✗ [{image_idx}/{len(pending)}] {file_name} "
                        f"→ ERROR after {elapsed:.1f}s: {exc}"
                    )
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
