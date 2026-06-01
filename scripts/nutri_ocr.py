from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(PROJECT_ROOT / ".cache" / "paddlex"))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")

try:
    from paddleocr import PaddleOCR
except ModuleNotFoundError:  # pragma: no cover - runtime dependency guard
    PaddleOCR = None


ANCHOR_PATTERN = re.compile(r"^(?P<product>.+) \((?P<anchor>\d+)\)\.(?P<ext>png|jpg|jpeg|webp)$", re.IGNORECASE)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="영양제 이미지에 PaddleOCR을 실행해 전체 텍스트를 추출하고 결과를 Excel로 저장한다."
    )
    parser.add_argument("--data-dir", default="data/영양제", help="Directory containing source images.")
    parser.add_argument("--output", default="data/result/nutri_results.xlsx", help="Excel output path.")
    parser.add_argument("--lang", default="korean", help="PaddleOCR language code.")
    return parser.parse_args()


def iter_target_images(data_dir: Path) -> Iterable[Path]:
    files = []
    for path in data_dir.iterdir():
        if not path.is_file():
            continue
        match = ANCHOR_PATTERN.match(path.name)
        if not match:
            continue
        files.append(path)
    return sorted(files)


def flatten_ocr_result(result: object) -> str:
    texts: list[str] = []
    if not isinstance(result, list):
        return ""

    for block in result:
        rec_texts = None
        if isinstance(block, dict):
            rec_texts = block.get("rec_texts")
        elif hasattr(block, "get"):
            rec_texts = block.get("rec_texts")
        if not isinstance(rec_texts, list):
            continue
        for text in rec_texts:
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
    return "\n".join(texts)


def extract_product_name(path: Path) -> str:
    match = ANCHOR_PATTERN.match(path.name)
    if not match:
        raise ValueError(f"Unexpected filename format: {path.name}")
    return match.group("product")


def extract_anchor_yn(path: Path) -> str:
    match = ANCHOR_PATTERN.match(path.name)
    if not match:
        raise ValueError(f"Unexpected filename format: {path.name}")
    return "Y" if match.group("anchor") == "0" else "N"


def load_ground_truth_text(data_dir: Path, product_name: str) -> str:
    txt_path = data_dir / f"{product_name}.txt"
    if not txt_path.exists():
        return ""
    return txt_path.read_text(encoding="utf-8").strip()


def normalize_for_comparison(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[^0-9a-z가-힣]+", "", normalized)
    return normalized


def calculate_ocr_result(ground_truth_text: str, ocr_text: str) -> str:
    ground_truth_normalized = normalize_for_comparison(ground_truth_text)
    ocr_normalized = normalize_for_comparison(ocr_text)

    if not ground_truth_normalized:
        return "N/A"

    matcher = difflib.SequenceMatcher(a=ground_truth_normalized, b=ocr_normalized)
    matched_chars = sum(block.size for block in matcher.get_matching_blocks())
    total_chars = len(ground_truth_normalized)
    score = matched_chars / total_chars
    return f"{score:.2%} ({matched_chars}/{total_chars})"


def save_rows_to_excel(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        rows,
        columns=[
            "Index",
            "File Path",
            "Product Name",
            "Anchor YN",
            "OCR Text",
            "OCR Result",
        ],
    )
    df.to_excel(output_path, index=False)


def load_existing_rows(output_path: Path) -> dict[str, dict[str, str]]:
    if not output_path.exists():
        return {}

    df = pd.read_excel(output_path).fillna("")
    existing_rows: dict[str, dict[str, str]] = {}
    for row in df.to_dict(orient="records"):
        file_path = str(row.get("File Path", "")).strip()
        if file_path:
            existing_rows[file_path] = {str(key): str(value) for key, value in row.items()}
    return existing_rows


def main() -> int:
    args = parse_args()

    if PaddleOCR is None:
        print(
            "Missing dependency: paddleocr. Install it first, for example:\n"
            "  pip install paddleocr paddlepaddle",
            file=sys.stderr,
        )
        return 1

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    image_paths = list(iter_target_images(data_dir))
    if not image_paths:
        print("No matching images found.", file=sys.stderr)
        return 1

    log(f"Started OCR export for {len(image_paths)} image(s).")
    output_path = Path(args.output)
    existing_rows = load_existing_rows(output_path)
    rows: list[dict[str, str]] = []
    ocr = None

    for index, image_path in enumerate(image_paths, start=1):
        product_name = extract_product_name(image_path)
        anchor_yn = extract_anchor_yn(image_path)
        ground_truth_text = load_ground_truth_text(data_dir, product_name)
        existing_row = existing_rows.get(str(image_path), {})

        ocr_text = existing_row.get("OCR Text", "").strip()
        ocr_result = existing_row.get("OCR Result", "").strip()
        if not ocr_text or not ocr_result:
            try:
                if ocr is None:
                    if PaddleOCR is None:
                        raise ModuleNotFoundError("paddleocr")
                    ocr = PaddleOCR(lang=args.lang)
                result = ocr.predict(str(image_path))
                ocr_text = flatten_ocr_result(result)
                ocr_result = calculate_ocr_result(ground_truth_text, ocr_text)
            except Exception as exc:  # pragma: no cover - runtime safety for batch export
                ocr_text = f"ERROR: {exc}"
                ocr_result = "ERROR"

        rows.append(
            {
                "Index": index,
                "File Path": str(image_path),
                "Product Name": product_name,
                "Anchor YN": anchor_yn,
                "OCR Text": ocr_text,
                "OCR Result": ocr_result,
            }
        )
        log(f"[OCR {index}/{len(image_paths)}] Finished image: {image_path.name} | OCR Result: {ocr_result}")
        if index == 1 or index % 10 == 0 or index == len(image_paths):
            save_rows_to_excel(rows, output_path)
            log(f"[OCR {index}/{len(image_paths)}] Saved intermediate Excel through: {image_path.name}")

    save_rows_to_excel(rows, output_path)
    log(f"Saved Excel file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
