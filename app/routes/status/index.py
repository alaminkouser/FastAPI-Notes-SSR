from fastapi import APIRouter
from pydantic import BaseModel
from app.tools.firebase import client

status_router = APIRouter()

class StatusResponse(BaseModel):
    firestore: bool

class Ok(BaseModel):
    ok: bool

@status_router.get("/")
def status() -> StatusResponse:
    doc = client.collection("ok").document("0").get()
    if not doc.exists:
        return StatusResponse(firestore=False)
    doc_dict = doc.to_dict()
    if doc_dict is None:
        return StatusResponse(firestore=False)
    data = Ok(**doc_dict)
    if data.ok:
        return StatusResponse(firestore=True)
    return StatusResponse(firestore=False)
