from fastapi import APIRouter

from app.question_bank import get_read_select_batch

router = APIRouter(prefix="/read-select", tags=["read-select"])


@router.get("/questions")
def get_questions(count: int = 10):
    items = get_read_select_batch(count)
    return {"items": items}
