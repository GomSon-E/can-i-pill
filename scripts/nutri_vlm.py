from __future__ import annotations

import argparse
import base64
import difflib
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


ANCHOR_PATTERN = re.compile(
    r"^(?P<product>.+) \((?P<anchor>\d+)\)\.(?P<ext>png|jpg|jpeg|webp)$",
    re.IGNORECASE,
)

EXPECTED_COLUMNS = [
    "Index",
    "File Path",
    "Product Name",
    "Anchor YN",
    "OCR Text",
    "OCR Result",
    "VLM Text",
    "VLM Result",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read an existing nutri_results.xlsx, run a VLM on each image, "
            "and fill the VLM Text and VLM Result columns. OCR columns are left untouched."
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
        help="Re-run VLM for every row, overwriting any existing VLM Text/Result values.",
    )
    return parser.parse_args()


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


def run_vlm_single(ollama_url: str, model_name: str, image_path: Path) -> str:
    prompt = (
        "이 이미지에 보이는 모든 글자를 그대로 추출하세요. "
        "설명, 해석, 요약, 머리말, 마무리 문장 없이 오직 추출한 텍스트만 출력하세요. "
        "줄바꿈은 자유롭게 사용 가능합니다."
    )
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
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

    text = raw_content
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", text)
        if text.endswith("```"):
            text = text[: -len("```")]
        text = text.strip()
    return text


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("VLM Text", "VLM Result"):
        if col not in df.columns:
            df[col] = ""
    df["VLM Text"] = df["VLM Text"].astype(str)
    df["VLM Result"] = df["VLM Result"].astype(str)

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

    total = len(df)
    def is_pending(i: int) -> bool:
        if args.force:
            return True
        vlm_text = str(df.at[i, "VLM Text"])
        vlm_result = str(df.at[i, "VLM Result"])
        if not vlm_text.strip() or not vlm_result.strip():
            return True
        if vlm_text.startswith("ERROR:") or vlm_result == "ERROR":
            return True
        return False

    pending_total = sum(
        1 for indices in products.values() for i in indices if is_pending(i)
    )
    log(
        f"Loaded {total} rows across {len(products)} products. "
        f"VLM pending: {pending_total}, already filled: {total - pending_total}."
    )
    log(f"Using VLM model: {args.vlm_model} @ {args.ollama_url}")

    overall_start = time.monotonic()
    processed = 0
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
                log(f"    → [{image_idx}/{len(pending)}] {file_name} ... calling VLM")
                image_start = time.monotonic()
                try:
                    vlm_text = run_vlm_single(args.ollama_url, args.vlm_model, image_path)
                    score = calculate_match_score(ground_truth_text, vlm_text)
                    df.at[i, "VLM Text"] = vlm_text
                    df.at[i, "VLM Result"] = score
                    elapsed = time.monotonic() - image_start
                    log(
                        f"    ✓ [{image_idx}/{len(pending)}] {file_name} "
                        f"→ {score} ({elapsed:.1f}s, {len(vlm_text)} chars)"
                    )
                except Exception as exc:
                    elapsed = time.monotonic() - image_start
                    df.at[i, "VLM Text"] = f"ERROR: {exc}"
                    df.at[i, "VLM Result"] = "ERROR"
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
