from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

# 시드 매칭 로직 재사용(동일 개념 사전으로 커버리지 편향 샘플링).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from label_scenarios import asked_concepts, concepts_of  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 질문 대상(asked_item) 풀 — **한국인에게 익숙한** 음식/시판약/영양제로 한정.
# (생소한 허브: 쏘팔메토·피버퓨·카바·에키네시아·아슈와간다·호로파·산사·
#  레스베라트롤 등은 제외.) 모두 시드 테이블 커버 가능 항목 위주.
ASKED_ITEMS: list[tuple[str, str]] = [
    # 음식/음료
    ("자몽", "food"),
    ("자몽주스", "food"),
    ("우유", "food"),
    ("커피", "food"),
    ("녹차", "food"),
    ("마늘", "food"),
    ("생강", "food"),
    ("술", "food"),
    ("낫토", "food"),
    ("시금치", "food"),
    ("청국장", "food"),
    ("두유", "food"),
    ("바나나", "food"),
    ("감초차", "food"),
    # 시판약(OTC)
    ("타이레놀", "otc"),
    ("게보린", "otc"),
    # 영양제/건강기능식품
    ("홍삼", "supplement"),
    ("인삼", "supplement"),
    ("은행잎추출물", "supplement"),
    ("오메가3", "supplement"),
    ("칼슘제", "supplement"),
    ("철분제", "supplement"),
    ("마그네슘", "supplement"),
    ("글루코사민", "supplement"),
    ("비타민C", "supplement"),
    ("비타민D", "supplement"),
    ("멜라토닌", "supplement"),
    ("홍국", "supplement"),
    ("강황", "supplement"),
    ("밀크씨슬", "supplement"),
]


def profile_concept_set(
    prescriptions: list[dict[str, Any]], supplements: list[dict[str, Any]]
) -> set[str]:
    cons: set[str] = set()
    for p in prescriptions:
        for d in p.get("drugs", []):
            cons |= concepts_of(d.get("ingredientName", ""))
    for s in supplements:
        cons |= concepts_of(f"{s.get('productName','')} {s.get('ingredients','')}")
    return cons


def asked_matches_profile(
    asked_item: str, profile_cons: set[str], cases: list[dict[str, Any]]
) -> bool:
    """질문 대상이 프로필과 시드 케이스로 매칭되는지(라벨 가능 여부)."""
    a = asked_concepts(asked_item)
    if not a:
        return False
    for c in cases:
        dcon = concepts_of(c.get("drug", ""))
        cp = concepts_of(c.get("counterpart", ""))
        if (a & cp and profile_cons & dcon) or (a & dcon and profile_cons & cp):
            return True
    return False

UNIT_PATTERN = re.compile(
    r"([가-힣A-Za-z][가-힣A-Za-z·\-]*)\s*([\d][\d.,]*)\s*"
    r"(mg|g|IU|㎍|ug|mcg|억\s*CFU|억\s*마리|kcal)",
)


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else PROJECT_ROOT / path


def clean_classification(value: Any) -> str:
    """text.json의 분류 라벨을 용도명 후보로 정리."""
    if not isinstance(value, str):
        return ""
    text = value.strip().strip("[]").strip()
    return text


def derive_usage_name(drug: dict[str, Any], prescription_name: str) -> str:
    """약물의 용도명(쉬운 말). 분류가 있으면 사용, 없으면 처방전명 기반."""
    classification = clean_classification(drug.get("분류"))
    if classification:
        return classification
    return f"{prescription_name} 관련약"


def summarize_ingredients(raw_text: str, product_name: str) -> str:
    """영양제 .txt에서 '성분 + 함량' 패턴을 추려 짧은 성분 요약 생성."""
    normalized = re.sub(r"\s+", " ", raw_text)
    seen: list[str] = []
    for match in UNIT_PATTERN.finditer(normalized):
        name = match.group(1).strip("·-")
        amount = match.group(2)
        unit = re.sub(r"\s+", "", match.group(3))
        # 열량/탄단지/나트륨 등 영양성분 잡정보는 제외
        if name in {"열량", "탄수화물", "단백질", "지방", "나트륨", "당류"}:
            continue
        token = f"{name} {amount}{unit}"
        if token not in seen:
            seen.append(token)
        if len(seen) >= 5:
            break
    if seen:
        return ", ".join(seen)
    # 폴백: 제품명에서 핵심 키워드만
    return product_name


def load_prescriptions(text_json_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(text_json_path.read_text(encoding="utf-8"))
    prescriptions: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("처방전", "")).strip()
        drugs_raw = item.get("의약품") or []
        if not name or not drugs_raw:
            continue
        drugs: list[dict[str, Any]] = []
        for drug in drugs_raw:
            if not isinstance(drug, dict):
                continue
            ingredient = str(drug.get("약품명", "")).strip()
            if not ingredient:
                continue
            drugs.append(
                {
                    "usageName": derive_usage_name(drug, name),
                    "ingredientName": ingredient,
                    "isCondition": True,
                }
            )
        if drugs:
            prescriptions.append(
                {
                    "condition": name,
                    "name": f"{name} 처방전",
                    "drugs": drugs,
                }
            )
    return prescriptions


def load_supplements(supplement_dir: Path) -> list[dict[str, str]]:
    supplements: list[dict[str, str]] = []
    for txt_path in sorted(supplement_dir.glob("*.txt")):
        product_name = txt_path.stem
        raw_text = txt_path.read_text(encoding="utf-8", errors="ignore")
        supplements.append(
            {
                "productName": product_name,
                "ingredients": summarize_ingredients(raw_text, product_name),
            }
        )
    return supplements


def choose_split(rng: random.Random, n_presc_pool: int, n_supp_pool: int) -> tuple[int, int]:
    """처방전 개수 + 영양제 개수 = 1~5 (각 개수 >= 0, 합 1~5)."""
    total = rng.randint(1, 5)
    # 가능한 (처방전 수, 영양제 수) 분할 후보를 만들고 무작위 선택
    candidates: list[tuple[int, int]] = []
    for n_presc in range(0, total + 1):
        n_supp = total - n_presc
        if n_presc <= n_presc_pool and n_supp <= n_supp_pool:
            candidates.append((n_presc, n_supp))
    return rng.choice(candidates)


def build_user(rng: random.Random) -> dict[str, Any]:
    gender = rng.choice(["female", "male"])
    birth_year = rng.randint(1960, 1975)  # 5060대
    return {"birthYear": birth_year, "gender": gender}


def build_scenario(
    rng: random.Random,
    index: int,
    prescriptions_pool: list[dict[str, Any]],
    supplements_pool: list[dict[str, str]],
    seed_cases: list[dict[str, Any]],
    coverage_prob: float,
    usage: dict[str, int],
) -> dict[str, Any]:
    n_presc, n_supp = choose_split(rng, len(prescriptions_pool), len(supplements_pool))
    chosen_presc = rng.sample(prescriptions_pool, n_presc) if n_presc else []
    chosen_supp = rng.sample(supplements_pool, n_supp) if n_supp else []

    conditions = [p["condition"] for p in chosen_presc]
    prescriptions = [{"name": p["name"], "drugs": p["drugs"]} for p in chosen_presc]
    supplements = [
        {"productName": s["productName"], "ingredients": s["ingredients"]}
        for s in chosen_supp
    ]

    # 커버리지 편향: 프로필을 먼저 정한 뒤, 그 프로필과 시드로 매칭되는
    # 질문 대상을 우선 선택(coverage_prob 확률). 매칭 후보가 없거나 미당첨이면
    # 전체 풀에서 무작위(자연스러운 '근거부족' 케이스도 일부 포함).
    profile_cons = profile_concept_set(prescriptions, supplements)
    covered = [it for it in ASKED_ITEMS if asked_matches_profile(it[0], profile_cons, seed_cases)]
    pick_pool = covered if (covered and rng.random() < coverage_prob) else ASKED_ITEMS
    # 다양성: 후보 중 지금까지 가장 적게 쓰인 항목 우선(동률은 무작위) → 특정
    # 항목(철분제·칼슘제 등) 쏠림 방지.
    min_used = min(usage[it[0]] for it in pick_pool)
    least_used = [it for it in pick_pool if usage[it[0]] == min_used]
    asked_item, asked_kind = rng.choice(least_used)
    usage[asked_item] = usage.get(asked_item, 0) + 1

    return {
        "id": f"SC-{index:02d}",
        "question": f"{asked_item} 먹어도 되나요?",
        "asked_item": asked_item,
        "asked_item_kind": asked_kind,
        "expected_level": None,
        "user": build_user(rng),
        "health": {
            "conditions": conditions,
            "customConditions": [],
            "hasAllergy": False,
            "allergies": [],
        },
        "prescriptions": prescriptions,
        "supplements": supplements,
        "expected_interaction_note": None,
        "rationale_source": None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "실제 보유 data(처방전/영양제)에서 랜덤 샘플링하여 상호작용 분석 "
            "테스트 시나리오를 생성한다. 처방전은 처방전 단위로 통째 선택하고, "
            "(처방전 개수 + 영양제 개수)의 합이 1~5종이 되도록 한다. "
            "질문 대상은 data와 무관하게 음식/시판약/영양제 풀에서 샘플링한다."
        )
    )
    parser.add_argument("--rx-json", default="data/처방전/text.json")
    parser.add_argument("--supplement-dir", default="data/영양제")
    parser.add_argument("--output", default="data/interaction_scenarios.json")
    parser.add_argument("--seed-table", default="data/interaction_seed_table.json")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--coverage-prob",
        type=float,
        default=0.75,
        help="시드 커버 질문 대상을 우선 선택할 확률(0~1). 0이면 순수 무작위.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rx_json = resolve_project_path(args.rx_json)
    supplement_dir = resolve_project_path(args.supplement_dir)
    output_path = resolve_project_path(args.output)

    if not rx_json.exists():
        print(f"처방전 JSON 없음: {rx_json}")
        return 1
    if not supplement_dir.exists():
        print(f"영양제 디렉터리 없음: {supplement_dir}")
        return 1

    prescriptions_pool = load_prescriptions(rx_json)
    supplements_pool = load_supplements(supplement_dir)
    seed_cases = json.loads(resolve_project_path(args.seed_table).read_text(encoding="utf-8"))["cases"]
    print(
        f"풀: 처방전 {len(prescriptions_pool)}종, 영양제 {len(supplements_pool)}종, "
        f"시드 케이스 {len(seed_cases)}건 (coverage_prob={args.coverage_prob})"
    )

    rng = random.Random(args.seed)
    usage: dict[str, int] = {name: 0 for name, _ in ASKED_ITEMS}
    scenarios = [
        build_scenario(
            rng, i + 1, prescriptions_pool, supplements_pool, seed_cases,
            args.coverage_prob, usage,
        )
        for i in range(args.count)
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 분포 요약
    kind_counts: dict[str, int] = {}
    size_counts: dict[int, int] = {}
    for sc in scenarios:
        kind_counts[sc["asked_item_kind"]] = kind_counts.get(sc["asked_item_kind"], 0) + 1
        size = len(sc["prescriptions"]) + len(sc["supplements"])
        size_counts[size] = size_counts.get(size, 0) + 1

    print(f"생성: {len(scenarios)}개 → {output_path}")
    print(f"질문 대상 종류 분포: {dict(sorted(kind_counts.items()))}")
    print(f"프로필 종 수(처방전+영양제) 분포: {dict(sorted(size_counts.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
