from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import app.store as store_module

router = APIRouter()


class UserCreate(BaseModel):
    nickname: str
    year: str
    month: str
    day: str
    gender: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    last_prescription_check: Optional[str] = None


@router.post("/user")
def create_user(body: UserCreate):
    user = {
        "nickname": body.nickname,
        "year": body.year,
        "month": body.month,
        "day": body.day,
        "gender": body.gender,
        "last_prescription_check": None,
    }
    store_module.store["user"] = user
    return user


@router.get("/user")
def get_user():
    user = store_module.store["user"]
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/user")
def update_user(body: UserUpdate):
    user = store_module.store["user"]
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if body.nickname is not None:
        user["nickname"] = body.nickname
    if body.last_prescription_check is not None:
        user["last_prescription_check"] = body.last_prescription_check
    return user
