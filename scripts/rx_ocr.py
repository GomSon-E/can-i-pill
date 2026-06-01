from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

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


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
EXCEL_COLUMNS = ["Index", "File Path", "OCR Text", "OCR Result"]
TOKEN_PATTERN = re.compile(r"[0-9A-Za-z가-힣.%]+")

# 채점 규칙: 정답 토큰 집계 시 제외/정규화할 키
EXCLUDED_TOP_LEVEL_KEYS = {"처방전", "질환명", "질병분류기호"}
UNIT_STRIPPED_KEYS = {"1회투약량"}


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run PaddleOCR on images under data/처방전 and export Text/Result columns to Excel."
        )
    )
    parser.add_argument(
        "--data-dir",
        default="data/처방전",
        help="Directory containing prescription images.",
    )
    parser.add_argument(
        "--output",
        default="data/result/rx_results.xlsx",
        help="Excel output path.",
    )
    parser.add_argument(
        "--lang",
        default="korean",
        help="PaddleOCR language code.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run OCR even if the output Excel already has a row for the file.",
    )
    return parser.parse_args()


def iter_image_paths(data_dir: Path) -> Iterable[Path]:
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


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


def calculate_ocr_result(file_path: Path, ocr_text: str, answer_map: dict[str, set[str]]) -> str:
    key = normalize_prescription_name(file_path.stem)
    answer_tokens = answer_map.get(key)
    if not answer_tokens:
        return "N/A"

    ocr_tokens = {
        normalized
        for token in TOKEN_PATTERN.findall(ocr_text)
        for normalized in [normalize_token(token)]
        if normalized
    }
    matched_count = sum(1 for token in answer_tokens if token in ocr_tokens)
    total_count = len(answer_tokens)
    score = matched_count / total_count if total_count else 0
    return f"{score:.2%} ({matched_count}/{total_count})"


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


def save_rows_to_excel(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=EXCEL_COLUMNS)
    df.to_excel(output_path, index=False)


def main() -> int:
    args = parse_args()

    if PaddleOCR is None:
        print(
            "Missing dependency: paddleocr. Install it first, for example:\n"
            "  pip install paddleocr paddlepaddle pandas openpyxl",
            file=sys.stderr,
        )
        return 1

    data_dir = resolve_project_path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    answer_map = load_answer_map(data_dir / "text.json")

    image_paths = list(iter_image_paths(data_dir))
    if not image_paths:
        print(f"No image files found under: {data_dir}", file=sys.stderr)
        return 1

    log(f"Started OCR export for {len(image_paths)} image(s).")
    output_path = resolve_project_path(args.output)
    existing_rows = load_existing_rows(output_path)
    rows: list[dict[str, str]] = []
    ocr = None

    for index, image_path in enumerate(image_paths, start=1):
        file_path = str(image_path)
        existing_row = existing_rows.get(file_path, {})

        text = existing_row.get("OCR Text", "").strip()

        should_run_ocr = args.force or not text or text.startswith("ERROR:")
        if should_run_ocr:
            try:
                if ocr is None:
                    ocr = PaddleOCR(lang=args.lang)
                result = ocr.predict(file_path)
                text = flatten_ocr_result(result)
            except Exception as exc:  # pragma: no cover - runtime safety for batch export
                text = f"ERROR: {exc}"

        if text.startswith("ERROR:"):
            result_payload = "ERROR"
        else:
            result_payload = calculate_ocr_result(image_path, text, answer_map)

        rows.append(
            {
                "Index": index,
                "File Path": file_path,
                "OCR Text": text,
                "OCR Result": result_payload,
            }
        )
        log(f"[OCR {index}/{len(image_paths)}] Finished image: {image_path.name} | OCR Result: {result_payload}")

        if index == 1 or index % 10 == 0 or index == len(image_paths):
            save_rows_to_excel(rows, output_path)
            log(f"[OCR {index}/{len(image_paths)}] Saved intermediate Excel through: {image_path.name}")

    save_rows_to_excel(rows, output_path)
    log(f"Saved Excel file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
