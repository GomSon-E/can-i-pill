import itertools
from fastapi import APIRouter, File, UploadFile
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
        "nutrients": [
            {"ingredient": "아스코르브산", "amount": "1000", "unit": "mg"},
            {"ingredient": "히아루론산", "amount": "50", "unit": "mg"},
        ],
    },
    {
        "name": "홍삼정 EX",
        "nutrients": [
            {"ingredient": "홍삼농축액", "amount": "70", "unit": "mg"},
            {"ingredient": "진세노사이드", "amount": "6", "unit": "mg"},
            {"ingredient": "비타민C", "amount": "50", "unit": "mg"},
        ],
    },
])


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ''


_OCR_MOCKS = itertools.cycle([
    {
        "name": "내과 처방전 2026-05",
        "drugs": [
            {
                "name": "메트포르민",
                "dosage": "500mg",
                "frequency": "1일 2회",
                "days": 30,
                "usage": "식후",
                "cautions": "저혈당 주의"
            },
            {
                "name": "아스피린",
                "dosage": "100mg",
                "frequency": "1일 1회",
                "days": 30,
                "usage": "식후",
                "cautions": "위장장애 가능"
            },
        ],
    },
    {
        "name": "정형외과 처방전 2026-05",
        "drugs": [
            {
                "name": "세레콕시브",
                "dosage": "200mg",
                "frequency": "1일 2회",
                "days": 14,
                "usage": "식후",
                "cautions": "위궤양 가능성"
            },
            {
                "name": "에소메프라졸",
                "dosage": "20mg",
                "frequency": "1일 1회",
                "days": 14,
                "usage": "아침 공복",
                "cautions": "장기복용 제한"
            },
            {
                "name": "트라마돌",
                "dosage": "50mg",
                "frequency": "필요시 4-6시간마다",
                "days": 7,
                "usage": "식후",
                "cautions": "졸음, 의존성 주의"
            },
        ],
    },
])


@router.post("/ocr")
def ocr(image: UploadFile = File(...)):
    return next(_OCR_MOCKS)


@router.post("/label")
def label(image: UploadFile = File(...)):
    return next(_LABEL_MOCKS)


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    mock = next(_ANALYZE_MOCKS)
    return {**mock, "detail": f"질문: {body.question} / 컨텍스트: {body.context}"}
