from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_history, get_stats, save_attempt

router = APIRouter(prefix="/history", tags=["history"])


class HistoryLogRequest(BaseModel):
    task_type: str
    score: float
    detail: dict


@router.get("")
def read_history(task_type: Optional[str] = None, limit: int = 50):
    entries = get_history(task_type=task_type, limit=limit)
    return {"entries": entries}


@router.get("/stats")
def read_stats():
    stats = get_stats()
    return {"stats": stats}


@router.post("/log")
def log_history(payload: HistoryLogRequest):
    return save_attempt(payload.task_type, payload.score, payload.detail)
