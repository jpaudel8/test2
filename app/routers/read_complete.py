from fastapi import APIRouter

from app.question_bank import get_read_complete_batch

router = APIRouter(prefix="/read-complete", tags=["read-complete"])


@router.get("/questions")
def get_questions(count: int = 5):
    items = get_read_complete_batch(count)
    return {"items": items}
