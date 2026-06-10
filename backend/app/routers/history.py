from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import app.store as store_module
from datetime import date

router = APIRouter()


class Opinion(BaseModel):
    summary: str
    detail: str


class AnalyzeItem(BaseModel):
    name: str
    level: str
    doctorOpinion: Opinion
    pharmacistOpinion: Opinion
    alternatives: list[str] = []


class HistoryCreate(BaseModel):
    level: str
    question: str
    doctorOpinion: Opinion | None = None
    pharmacistOpinion: Opinion | None = None
    alternatives: list[str] = []
    items: list[AnalyzeItem] = []


@router.get("/history")
def get_history():
    return {"history": list(reversed(store_module.store["history"]))}


@router.get("/history/{history_id}")
def get_history_item(history_id: str):
    for item in store_module.store["history"]:
        if item["id"] == history_id:
            return item
    raise HTTPException(status_code=404, detail="History item not found")


@router.post("/history")
def create_history(body: HistoryCreate):
    item = {
        "id": str(uuid.uuid4()),
        "level": body.level,
        "question": body.question,
        "alternatives": body.alternatives,
        "created_at": str(date.today()),
    }
    if body.doctorOpinion is not None:
        item["doctorOpinion"] = body.doctorOpinion.model_dump()
    if body.pharmacistOpinion is not None:
        item["pharmacistOpinion"] = body.pharmacistOpinion.model_dump()
    if body.items:
        item["items"] = [analysis_item.model_dump() for analysis_item in body.items]
    store_module.store["history"].append(item)
    return item
