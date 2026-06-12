MOCK_OCR_RESPONSE = {
    "name": "Mock 처방전",
    "drugs": [
        {
            "name": "메트포르민",
            "dosage": "500mg",
            "frequency": "1일 2회",
            "days": 30,
            "usage": "식후",
            "cautions": "",
        }
    ],
}

MOCK_LABEL_RESPONSE = {
    "name": "Mock 영양제",
    "nutrients": [
        {"ingredient": "비타민C", "amount": "500", "unit": "mg"}
    ],
}

MOCK_ANALYZE_RESPONSE = {
    "level": "caution",
    "doctorOpinion": {"summary": "Mock 의사 의견", "detail": "Mock 상세 설명"},
    "pharmacistOpinion": {"summary": "Mock 약사 의견", "detail": "Mock 상세 설명"},
    "alternatives": [],
}
