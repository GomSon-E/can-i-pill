import itertools
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

router = APIRouter()

_ANALYZE_MOCKS = itertools.cycle([
    {
        "level": "safe",
        "doctorOpinion": {
            "summary": "현재 복용 중인 약과 상호작용이 없습니다.",
            "detail": "권장 용량을 지켜 복용하세요. 특별한 주의사항은 없습니다."
        },
        "pharmacistOpinion": {
            "summary": "안전한 조합입니다.",
            "detail": "약물 간 상호작용이 없으므로 안심하고 복용하셔도 됩니다."
        },
        "alternatives": [],
    },
    {
        "level": "caution",
        "doctorOpinion": {
            "summary": "함께 복용 시 위장 장애가 생길 수 있어요.",
            "detail": "식후 복용을 권장합니다. 위장불편감이 나타나면 의사에게 보고하세요."
        },
        "pharmacistOpinion": {
            "summary": "주의가 필요합니다.",
            "detail": "두 약물의 상호작용으로 인해 위장 자극이 증가할 수 있습니다."
        },
        "alternatives": ["타이레놀 (아세트아미노펜)", "트라마돌"],
    },
    {
        "level": "danger",
        "doctorOpinion": {
            "summary": "현재 복용 중인 메트포르민과 심각한 상호작용이 있습니다.",
            "detail": "복용을 중단하고 의사와 상담하세요. 생명에 위협을 줄 수 있습니다."
        },
        "pharmacistOpinion": {
            "summary": "절대 함께 복용하면 안 됩니다.",
            "detail": "이 조합은 심각한 부작용을 초래할 수 있으므로 약사나 의사의 지시를 받으세요."
        },
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


class AnalyzeRequest(BaseModel):
    question: str
    context: str = ''


@router.post("/ocr")
def ocr(image: UploadFile = File(...)):
    return next(_OCR_MOCKS)


@router.post("/label")
def label(image: UploadFile = File(...)):
    return next(_LABEL_MOCKS)


@router.post("/analyze")
def analyze(body: AnalyzeRequest):
    return next(_ANALYZE_MOCKS)
