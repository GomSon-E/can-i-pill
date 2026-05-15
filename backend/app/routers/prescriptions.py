from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import app.store as store_module

router = APIRouter()


class Drug(BaseModel):
    name: str
    purpose: str


class PrescriptionCreate(BaseModel):
    name: str
    drugs: List[Drug]


@router.get("/prescriptions")
def get_prescriptions():
    return {"prescriptions": store_module.store["prescriptions"]}


@router.post("/prescriptions")
def create_prescription(body: PrescriptionCreate):
    prescription = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "drugs": [{"name": d.name, "purpose": d.purpose} for d in body.drugs],
    }
    store_module.store["prescriptions"].append(prescription)
    return prescription


@router.put("/prescriptions/{prescription_id}")
def update_prescription(prescription_id: str, body: PrescriptionCreate):
    prescriptions = store_module.store["prescriptions"]
    for i, p in enumerate(prescriptions):
        if p["id"] == prescription_id:
            updated = {
                "id": prescription_id,
                "name": body.name,
                "drugs": [{"name": d.name, "purpose": d.purpose} for d in body.drugs],
            }
            prescriptions[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Prescription not found")


@router.delete("/prescriptions/{prescription_id}")
def delete_prescription(prescription_id: str):
    prescriptions = store_module.store["prescriptions"]
    for i, p in enumerate(prescriptions):
        if p["id"] == prescription_id:
            prescriptions.pop(i)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Prescription not found")
