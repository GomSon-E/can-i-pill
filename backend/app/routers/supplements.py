from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import app.store as store_module

router = APIRouter()


class SupplementCreate(BaseModel):
    name: str
    ingredients: List[str]


class SupplementsBulkCreate(BaseModel):
    supplements: List[SupplementCreate]


@router.get("/supplements")
def get_supplements():
    return {"supplements": store_module.store["supplements"]}


@router.post("/supplements")
def create_supplements(body: SupplementsBulkCreate):
    for s in body.supplements:
        store_module.store["supplements"].append({
            "id": str(uuid.uuid4()),
            "name": s.name,
            "ingredients": s.ingredients,
        })
    return {"supplements": store_module.store["supplements"]}


@router.delete("/supplements/{supplement_id}")
def delete_supplement(supplement_id: str):
    supplements = store_module.store["supplements"]
    for i, s in enumerate(supplements):
        if s["id"] == supplement_id:
            supplements.pop(i)
            return {"supplements": store_module.store["supplements"]}
    raise HTTPException(status_code=404, detail="Supplement not found")
