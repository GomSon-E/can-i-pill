from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import app.store as store_module

router = APIRouter()


class HealthCreate(BaseModel):
    conditions: List[str]
    allergies: List[str]


@router.post("/health-info")
def create_health(body: HealthCreate):
    health = {
        "conditions": body.conditions,
        "allergies": body.allergies,
    }
    store_module.store["health"] = health
    return health


@router.get("/health-info")
def get_health():
    health = store_module.store["health"]
    if health is None:
        raise HTTPException(status_code=404, detail="Health info not found")
    return health
