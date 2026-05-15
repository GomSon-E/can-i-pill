import itertools
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

_ANALYZE_MOCKS = itertools.cycle([
    {
        "level": "safe",
        "summary": "현재 복용 중인 약과 상호작용이 없습니다. 권장 용량을 지켜 복용하세요.",
        "alternatives": [],
    },
    {
        "level": "caution",
        "summary": "함께 복용 시 위장 장애가 생길 수 있어요. 식후 복용을 권장합니다.",
        "alternatives": ["타이레놀 (아세트아미노펜)", "트라마돌"],
    },
    {
        "level": "danger",
        "summary": "현재 복용 중인 메트포르민과 심각한 상호작용이 있습니다. 복용을 중단하고 의사와 상담하세요.",
        "alternatives": ["아세트아미노펜", "나프록센"],
    },
])

_LABEL_MOCKS = itertools.cycle([
    {
        "name": "비타민C 1000mg",
        "ingredients": ["아스코르브산 1000mg", "히아루론산"],
    },
    {
        "name": "홍삼정 EX",
        "ingredients": ["홍삼농축액 70%", "진세노사이드 6mg", "비타민C 50mg"],
    },
])


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ''


_OCR_MOCKS = itertools.cycle([
    {
        "name": "내과 처방전 2026-05",
        "drugs": [
            {"name": "메트포르민", "purpose": "지병 약"},
            {"name": "아스피린", "purpose": "보조 약물"},
        ],
    },
    {
        "name": "정형외과 처방전 2026-05",
        "drugs": [
            {"name": "세레콕시브", "purpose": "지병 약"},
            {"name": "에소메프라졸", "purpose": "보조 약물"},
            {"name": "트라마돌", "purpose": "보조 약물"},
        ],
    },
])


@router.post("/ocr")
def ocr():
    return next(_OCR_MOCKS)


@router.post("/label")
def label():
    return next(_LABEL_MOCKS)


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    mock = next(_ANALYZE_MOCKS)
    return {**mock, "detail": f"질문: {body.question} / 컨텍스트: {body.context}"}
