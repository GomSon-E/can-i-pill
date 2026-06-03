from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 개념 사전: 개념명 -> {inc: 포함 패턴, exc: 제외 패턴}
# inc 패턴 중 하나라도 텍스트에 있고, exc 패턴이 전혀 없으면 해당 개념으로 태깅.
CONCEPTS: dict[str, dict[str, list[str]]] = {
    # --- 약물(주로 drug 측) ---
    "statin": {"inc": ["스타틴", "심바스타틴", "로바스타틴", "아토르바스타틴", "로수바스타틴"]},
    "warfarin": {"inc": ["와파린", "쿠마린", "항응고"]},
    "antiplatelet": {"inc": ["아스피린", "아세틸살리실산", "클로피도그렐", "티클로피딘", "항혈소판", "프로텍트"]},
    "buspirone": {"inc": ["부스피론"]},
    "ccb": {"inc": ["칼슘채널차단제", "암로디핀", "니페디핀", "펠로디핀", "베라파밀", "니카르디핀", "니모디핀", "니솔디핀", "카디핀", "이스라디핀"]},
    "antihypertensive": {"inc": ["혈압약", "혈압강하", "항고혈압", "로사르탄", "텔미사르탄", "발사르탄", "리시노프릴", "ARB", "ACE"]},
    "sedative_benzo": {"inc": ["벤조디아제핀", "벤조", "알프라졸람", "로라제팜", "디아제팜", "졸피뎀", "미다졸람", "트리아졸람", "진정", "수면제", "바르비투르"]},
    "ssri": {"inc": ["SSRI", "에스시탈로프람", "시탈로프람", "설트랄린", "세르트랄린", "플루옥세틴", "파록세틴", "항우울"]},
    "antipsychotic": {"inc": ["리스페리돈", "할로페리돌", "클로자핀", "아리피프라졸", "항정신병"]},
    "maoi": {"inc": ["MAOI", "모노아민산화효소"]},
    "bisphosphonate": {"inc": ["비스포스포네이트", "알렌드론", "리세드론", "이반드론"]},
    "thiazide_diuretic": {"inc": ["티아지드", "이뇨제", "하이드로클로로티아지드", "인다파미드", "클로르탈리돈"]},
    "digoxin": {"inc": ["디곡신", "강심", "강심배당체"]},
    "antidiabetic": {"inc": ["당뇨", "메트포르민", "글리메피리드", "시타글립틴", "테네리글립틴", "이메글리민", "인슐린", "설포닐우레아", "혈당강하", "글리부라이드", "피오글리타존", "글립틴"]},
    "ppi": {"inc": ["양성자펌프", "PPI", "에소메프라졸", "오메프라졸", "보노프라잔", "에소메졸", "위산억제"]},
    "nsaid": {"inc": ["NSAID", "이부프로펜", "세레콕시브", "셀레콕시브", "에토돌락", "디클로페낙", "소염진통", "나프록센"]},
    # 영문 표기(Acetaminophen/Paracetamol)와 복합제 브랜드(울트라셋=트라마돌+아세트아미노펜)도 포착.
    "acetaminophen": {"inc": ["아세트아미노펜", "파라세타몰", "아세타미노펜", "Acetaminophen", "Paracetamol", "울트라셋"]},
    # 주의: 테르페나딘·아스테미졸(자몽과 QT 위험, 시장 철수)은 일반 항히스타민과
    # 위험도가 전혀 달라 antihistamine 개념에 넣지 않는다(클로르페니라민 등과 혼동 방지).
    "antihistamine": {"inc": ["항히스타민", "클로르페니라민", "베포타스틴", "펙소페나딘", "디펜히드라민", "세티리진", "로라타딘"]},
    "beta_blocker": {"inc": ["베타차단제", "나돌롤", "프로프라놀롤", "카르베딜롤", "비소프롤롤"]},
    "levothyroxine": {"inc": ["레보티록신", "갑상선호르몬", "씬지로이드", "씬지록신"]},
    "quinolone": {"inc": ["퀴놀론", "시프로플록사신", "레보플록사신", "노르플록사신", "목시플록사신", "플록사신"]},
    "tetracycline": {"inc": ["테트라사이클린", "독시사이클린", "미노사이클린"]},
    "theophylline": {"inc": ["테오필린"]},
    "carbamazepine": {"inc": ["카르바마제핀"]},
    "phenytoin": {"inc": ["페니토인"]},
    "lithium": {"inc": ["리튬"]},
    "corticosteroid": {"inc": ["코르티코스테로이드", "스테로이드", "부데소니드", "프레드니솔론", "덱사메타손"]},
    "immunosuppressant": {"inc": ["면역억제", "시클로스포린", "사이클로스포린", "타크로리무스", "시롤리무스", "라파마이신"]},
    "antiviral_hiv": {"inc": ["항HIV", "항레트로바이러스", "프로테아제 억제제", "사퀴나비르", "인디나비르", "에파비렌즈", "리토나비르"]},
    "antiviral_other": {"inc": ["오셀타미비르", "발라시클로버", "아시클로버"]},
    "oral_contraceptive": {"inc": ["경구피임약", "피임약", "피임"]},
    "chemo": {"inc": ["항암", "이리노테칸", "독소루비신", "시클로포스파미드", "에토포시드", "보르테조밉", "파클리탁셀", "빈크리스틴", "메토트렉세이트", "타목시펜", "아로마타제", "닌테다닙", "랄록시펜", "도세탁셀", "캄토테신"]},
    "penicillamine": {"inc": ["페니실라민"]},
    "aluminum_antacid": {"inc": ["알루미늄", "제산제", "알마게이트", "수산화알루미늄"]},

    # --- 음식/허브/보충제(주로 counterpart 측) ---
    "grapefruit": {"inc": ["자몽"]},
    "vitaminK_food": {"inc": ["비타민K", "낫토", "시금치", "녹즙", "청국장", "녹색잎", "케일", "브로콜리"]},
    "ginkgo": {"inc": ["은행잎", "은행", "징코"]},
    "garlic": {"inc": ["마늘"]},
    "ginseng": {"inc": ["홍삼", "인삼"]},
    "omega3": {"inc": ["오메가3", "오메가-3", "어유", "EPA", "DHA"]},
    "stjohnswort": {"inc": ["세인트존스워트", "성요한", "세인트 존스"]},
    "calcium": {"inc": ["칼슘"], "exc": ["칼슘채널"]},
    "iron": {"inc": ["철분", "황산제일철", "페로바유", "철제"]},
    "magnesium": {"inc": ["마그네슘", "마그디아", "산화마그네슘"]},
    "zinc": {"inc": ["아연"]},
    "vitaminC": {"inc": ["비타민C", "아스코르빈산", "아스코르브산", "아스코르빈"]},
    "vitaminD": {"inc": ["비타민D", "콜레칼시페롤", "칼시페롤"]},
    "vitaminE": {"inc": ["비타민E", "토코페롤"]},
    "coq10": {"inc": ["코엔자임", "코큐텐", "코엔자임Q10", "Q10"]},
    "glucosamine": {"inc": ["글루코사민", "콘드로이틴"]},
    "greentea": {"inc": ["녹차", "EGCG"]},
    "milkthistle": {"inc": ["밀크씨슬", "실리마린", "sylimarin", "스티렌"]},
    "licorice": {"inc": ["감초"]},
    "kava": {"inc": ["카바"]},
    "turmeric": {"inc": ["강황", "커큐민", "울금"]},
    "ginger": {"inc": ["생강"]},
    "ashwagandha": {"inc": ["아슈와간다"]},
    "melatonin": {"inc": ["멜라토닌"]},
    "sawpalmetto": {"inc": ["쏘팔메토", "소팔메토"]},
    "echinacea": {"inc": ["에키네시아"]},
    "soy": {"inc": ["대두", "두유", "제니스테인", "이소플라본", "콩"]},
    "feverfew": {"inc": ["피버퓨", "화란국화"]},
    "redyeastrice": {"inc": ["홍국"]},
    "fenugreek": {"inc": ["호로파"]},
    "cinnamon": {"inc": ["계피", "시나몬"]},
    "resveratrol": {"inc": ["레스베라트롤"]},
    "hawthorn": {"inc": ["산사"]},
    "dongquai": {"inc": ["당귀"]},
    "cranberry": {"inc": ["크랜베리"]},
    "caffeine": {"inc": ["카페인", "커피", "에너지음료"]},
    "alcohol": {"inc": ["알코올", "술"]},
    "dairy": {"inc": ["우유", "유제품", "치즈"]},
    "tyramine": {"inc": ["티라민", "숙성치즈", "발효식품", "살라미", "레드와인"]},
}

# OTC 브랜드 → 개념 확장(질문 대상이 복합 시판약일 때)
BRAND_EXPANSION: dict[str, list[str]] = {
    "타이레놀": ["acetaminophen"],
    "게보린": ["acetaminophen", "caffeine"],
    "판콜에이": ["acetaminophen", "antihistamine", "caffeine"],
    "펜잘": ["acetaminophen", "caffeine"],
    "사리돈": ["acetaminophen", "caffeine"],
}


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


def concepts_of(text: str) -> set[str]:
    """텍스트에서 매칭되는 개념 집합."""
    if not text:
        return set()
    found: set[str] = set()
    for name, spec in CONCEPTS.items():
        inc = spec.get("inc", [])
        exc = spec.get("exc", [])
        if any(p in text for p in inc) and not any(p in text for p in exc):
            found.add(name)
    return found


def asked_concepts(asked_item: str) -> set[str]:
    c = concepts_of(asked_item)
    for brand, extra in BRAND_EXPANSION.items():
        if brand in asked_item:
            c.update(extra)
    return c


def profile_items(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """프로필(처방약+영양제) 항목별 개념 태깅."""
    items: list[dict[str, Any]] = []
    for p in scenario.get("prescriptions", []):
        for d in p.get("drugs", []):
            name = d.get("ingredientName", "")
            items.append({"kind": "drug", "name": name, "concepts": concepts_of(name)})
    for s in scenario.get("supplements", []):
        name = s.get("productName", "")
        ing = s.get("ingredients", "")
        items.append(
            {"kind": "supplement", "name": name, "concepts": concepts_of(f"{name} {ing}")}
        )
    return items


def match_scenario(
    scenario: dict[str, Any], cases: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]]]:
    """시나리오에 매칭되는 시드 케이스 탐색.

    Returns (proposed_level, matched[]).
    """
    a_con = asked_concepts(scenario.get("asked_item", ""))
    items = profile_items(scenario)

    matched: list[dict[str, Any]] = []
    for case in cases:
        # drug 측은 구체 약물명(drug 필드)으로만 태깅 — drug_class(예: '항히스타민제',
        # '항우울제')의 과일반화로 특정약 케이스가 클래스 전체에 잘못 걸리는 것 방지.
        drug_con = concepts_of(case.get("drug", ""))
        cp_con = concepts_of(case.get("counterpart", ""))

        # 어떤 프로필 항목이 케이스의 어느 측과 맞는지 찾는다.
        for it in items:
            ic = it["concepts"]
            hit = None
            # asked = counterpart(음식/보충제), profile item = drug(약)
            if (a_con & cp_con) and (ic & drug_con):
                hit = {"role": "asked=counterpart, profile=drug",
                       "via_asked": sorted(a_con & cp_con),
                       "via_profile": sorted(ic & drug_con)}
            # asked = drug(약, 예: 타이레놀), profile item = counterpart(음식/보충제)
            elif (a_con & drug_con) and (ic & cp_con):
                hit = {"role": "asked=drug, profile=counterpart",
                       "via_asked": sorted(a_con & drug_con),
                       "via_profile": sorted(ic & cp_con)}
            if hit:
                matched.append({
                    "case_id": case["id"],
                    "level": case["level"],
                    "drug": case["drug"],
                    "counterpart": case["counterpart"],
                    "effect": case.get("effect", ""),
                    "sources": case.get("sources", []),
                    "profile_item": it["name"],
                    **hit,
                })
                break  # 한 케이스는 한 번만 기록(첫 매칭 프로필 항목 기준)

    if not matched:
        return "insufficient_evidence", []
    levels = {m["level"] for m in matched}
    if "danger" in levels:
        return "danger", matched
    if "caution" in levels:
        return "caution", matched
    # 매칭이 safe 등급뿐 → 알려졌으나 임상적으로 무의미한 조합(예: 미네랄끼리 흡수경쟁)
    return "safe", matched


def write_review(scenarios: list[dict[str, Any]], path: Path) -> None:
    """사람 검토용 마크다운(매칭 근거 포함) 생성."""
    R: list[str] = []
    R.append("# 시나리오 자동 라벨 제안 — 사람 검토용\n")
    R.append("`label_status=auto_seed`는 시드 매칭 제안이며 **검토·확정 필요**. "
             "`insufficient_evidence`는 시드에 근거 없음 → '근거부족→전문가 상담'.\n")
    R.append("매칭 근거(via)는 클래스 단위라 과대평가 가능(예: 자몽×스타틴은 "
             "심바·로바·아토르바만 해당, 로수바·프라바는 영향 없음). 케이스 약물명과 "
             "프로필 약물명을 대조해 확정할 것.\n")
    for sc in scenarios:
        lvl = sc["label_status"] if sc["expected_level"] is None else sc["expected_level"]
        R.append(f"## {sc['id']} — “{sc['asked_item']}” → **{lvl}**")
        if not sc["matched_cases"]:
            R.append("- 매칭 없음\n")
            continue
        R.append("| 케이스 | level | 약물 | 대상 | 매칭된 프로필 약 | 근거(via) | 출처 |")
        R.append("|---|---|---|---|---|---|---|")
        for m in sc["matched_cases"]:
            via = f"asked={m['via_asked']} / profile={m['via_profile']}"
            R.append(f"| {m['case_id']} | {m['level']} | {m['drug']} | {m['counterpart']} "
                     f"| {m['profile_item']} | {via} | {', '.join(m['sources'])} |")
        R.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(R) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="시드 테이블 기반 시나리오 expected_level 자동 제안")
    ap.add_argument("--scenarios", default="data/interaction_scenarios.json")
    ap.add_argument("--seed", default="data/interaction_seed_table.json")
    ap.add_argument("--output", default="data/interaction_scenarios.labeled.json")
    ap.add_argument(
        "--review",
        default=None,
        help="사람 검토용 마크다운 경로(미지정 시 생성 안 함). labeled.json에 모든 정보가 이미 있음.",
    )
    args = ap.parse_args()

    scenarios = json.loads(resolve(args.scenarios).read_text(encoding="utf-8"))
    seed = json.loads(resolve(args.seed).read_text(encoding="utf-8"))
    cases = seed["cases"]

    counts = {"danger": 0, "caution": 0, "safe": 0, "insufficient_evidence": 0}
    for sc in scenarios:
        level, matched = match_scenario(sc, cases)
        if level == "insufficient_evidence":
            sc["expected_level"] = None
            sc["label_status"] = "insufficient_evidence"
        else:
            sc["expected_level"] = level
            sc["label_status"] = "auto_seed"  # 사람 검토 필요
        counts[level] += 1
        sc["matched_cases"] = matched
        sc["rationale_source"] = sorted({s for m in matched for s in m["sources"]})
    n_danger, n_caution, n_insuff = (
        counts["danger"], counts["caution"], counts["insufficient_evidence"]
    )
    n_safe = counts["safe"]

    out = resolve(args.output)
    out.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")

    # 사람 검토용 리뷰 마크다운(옵션). --review 지정 시에만 생성.
    # labeled.json에 expected_level·matched_cases·rationale_source가 모두 있으므로 기본은 생략.
    if args.review:
        write_review(scenarios, resolve(args.review))

    # 콘솔 요약
    print(f"시나리오 {len(scenarios)}개 라벨 제안 → {out}")
    print(f"  danger {n_danger} / caution {n_caution} / safe {n_safe} / insufficient_evidence {n_insuff}")
    print()
    print(f"{'ID':<7}{'asked_item':<14}{'level':<22}{'매칭 케이스'}")
    print("-" * 90)
    for sc in scenarios:
        ids = ", ".join(m["case_id"] for m in sc["matched_cases"]) or "-"
        lvl = sc["label_status"] if sc["expected_level"] is None else sc["expected_level"]
        print(f"{sc['id']:<7}{sc['asked_item']:<14}{lvl:<22}{ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
