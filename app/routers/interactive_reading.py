from fastapi import APIRouter

from app.question_bank import get_reading_passage

router = APIRouter(prefix="/interactive-reading", tags=["interactive-reading"])


@router.get("/passage")
def get_passage():
    return get_reading_passage()
