from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import app.store as store_module
from datetime import date

router = APIRouter()


class HistoryCreate(BaseModel):
    level: str
    question: str
    summary: str


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
        "summary": body.summary,
        "created_at": str(date.today()),
    }
    store_module.store["history"].append(item)
    return item
